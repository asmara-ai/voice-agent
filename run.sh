cd server
mv .env.sample .env

uv venv
source .venv/bin/activate
uv sync

cd mcp_servers/mcp-shopify
npm install
npm run build
cd ../../../
cd client

pnpm install 
pnpm run build

cd ../server
uv run app.py
