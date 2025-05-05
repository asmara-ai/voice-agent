# Customer Service Voice Agent

## Project Structure

- **`client/`**: Frontend source code directory
- **`server/`**: Backend source code directory
- **`.dockerignore`**: Specifies files and directories to exclude from the Docker build context  
- **`Dockerfile`**: Docker configuration file
- **`README.md`**: Project documentation

## Prerequisites

To run this project, you'll need the following installed on your system:

- **Python**: Version 3.12 or higher
- **Node.js**: Version 20.18
- **`uv`**: A Python package and project manager

## Installation

Follow these steps to set up and run the project.

### 1. Clone the Repository

Clone the repository to your local machine and update .env file:

```bash
git clone <repository-url>
cd voice-agent
```

### 2 Copy /server/.env.sample file with /server/.env and Update file.


### 3 run project

```bash
sh run.sh
```

## Running with Docker

You can also run the project using Docker, which will handle both the frontend and backend in a single container.

### 1. Update the .env File

Before building the Docker image, ensure you have updated the `.env` file in the `server/` directory with your desired environment variables (e.g., `OPENAI_API_KEY`, `BOT_LANGUAGE_NAME`, `BOT_LANGUAGE_CODE`). The Dockerfile will use these values during the build process.

### 2. Build the Docker Image

From the root directory of the project (where the Dockerfile is located), build the Docker image:

```bash
docker build -t voice-agent .
```

### 3. Run the Docker Container

Run the container, mapping port 8080 on your host to port 8080 in the container:

```bash
docker run -d -p 8080:8080 voice-agent
```

### 4. Access the Application

Once the container is running, you can access the application at:

```
http://localhost:8080
```
