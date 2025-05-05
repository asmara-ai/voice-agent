import asyncio
from typing import List, Dict, Any
from contextlib import AsyncExitStack
from dataclasses import dataclass
import traceback
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client, get_default_environment


@dataclass
class McpServer:
    name: str
    config: str
    status: str = "disconnected"
    error: str = ""
    tools: List[Dict[str, Any]] = None

    def __post_init__(self):
        self.tools = [] if self.tools is None else self.tools


@dataclass
class McpConnection:
    server: McpServer
    session: ClientSession
    transport: tuple[asyncio.StreamReader, asyncio.StreamWriter]
    exit_stack: AsyncExitStack


class MCPHub:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            print("Creating new MCPHub instance")
            cls._instance = super(MCPHub, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            print("Initializing MCPHub")
            self.connections: List[McpConnection] = []
            self._connection_tasks = {}
            self._connection_futures = {}
            self._initialized = True

    async def connect_to_server(self, name: str, config: Dict[str, Any]):
        """Connect to an MCP server.

        Args:
            name: Name of the server.
            config: Server configuration containing command, args, and env.
        """
        self._connection_futures[name] = asyncio.Future()

        server = McpServer(name=name, config=str(config), status="connecting")

        # Create a task for this connection
        connection_task = asyncio.create_task(
            self._maintain_connection(name, server, config)
        )
        self._connection_tasks[name] = connection_task
        await self._connection_futures[name]

    async def _maintain_connection(
        self, name: str, server: McpServer, config: Dict[str, Any]
    ):
        """Handle the lifecycle of a single connection"""
        exit_stack = AsyncExitStack()
        try:
            # Setup environment
            env = get_default_environment()
            server_env = config.get("env")
            if server_env:
                env.update(server_env)

            server_params = StdioServerParameters(
                command=config["command"], args=config["args"], env=env
            )

            # Start the stdio client connection
            stdio_transport = await exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            stdio, write = stdio_transport

            # Create an MCP session
            session = await exit_stack.enter_async_context(ClientSession(stdio, write))
            await session.initialize()

            # Create connection object
            connection = McpConnection(
                server=server,
                session=session,
                transport=stdio_transport,
                exit_stack=exit_stack,
            )

            connection.server.tools = await self.fetch_tools_list(connection)

            connection.server.status = "connected"
            connection.server.error = ""

            # Save connection
            self._connection_futures[name].set_result(connection)
            self.connections.append(connection)

            try:
                await asyncio.Future()  # Wait indefinitely
            except asyncio.CancelledError:
                print(f"Connection closed for server {name}")
                await exit_stack.aclose()
                raise

            print(
                f"\nConnected to server {name} with tools:",
                [tool["name"] for tool in connection.server.tools],
            )

        except Exception as e:
            print(f"Error connecting to server {name}: {e}")
            server.status = "disconnected"
            server.error = str(e)
            raise
        finally:
            # Cleanup connection from list if it exists
            self.connections = [
                conn for conn in self.connections if conn.server.name != name
            ]

    async def fetch_tools_list(self, connection: McpConnection) -> List[Dict[str, Any]]:
        """Fetch list of available tools from a server"""
        try:
            response = await connection.session.list_tools()
            return [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                }
                for tool in response.tools
            ]
        except Exception:
            return []

    async def call_tool(
        self, server_name: str, tool_name: str, tool_arguments: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Call a tool on a server with timeout"""
        connection = next(
            (conn for conn in self.connections if conn.server.name == server_name), None
        )
        if not connection:
            raise ValueError(f"No connection found for server: {server_name}")

        try:
            # Add 30 second timeout to prevent hanging
            response = await asyncio.wait_for(
                connection.session.call_tool(tool_name, tool_arguments or {}),
                timeout=30.0,
            )
            return {
                "content": [
                    {"type": content.type, "text": content.text}
                    for content in response.content
                ]
            }
        except asyncio.TimeoutError:
            error_msg = (
                f"Tool call to {tool_name} on {server_name} timed out after 30 seconds"
            )
            print(error_msg)
            return {"content": [{"type": "error", "text": error_msg}]}
        except Exception as e:
            error_msg = f"Error calling tool {tool_name} on {server_name}: {str(e)}"
            print(error_msg)
            return {"content": [{"type": "error", "text": error_msg}]}

    def get_servers(self) -> List[McpServer]:
        """Get list of all connected servers"""
        return [conn.server for conn in self.connections]

    async def cleanup(self):
        """Clean up all connections and resources"""
        for name, task in list(self._connection_tasks.items()):
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                print(f"Connection to {name} closed successfully")
            except Exception as e:
                print(traceback.format_exc())
                print(f"Error cleaning up connection: {str(e)}")
            finally:
                del self._connection_tasks[name]
