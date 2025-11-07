# Task Tracker MCP Server

## Overview

This project is a Model Context Protocol (MCP) server that acts as a bridge to a task-tracking application backend. It handles authentication against the backend and exposes a set of tools and resources that an MCP client (like a large language model or an AI assistant) can use to interact with the task management system.

The server is built using Python and the `fastmcp` library. On startup, it authenticates with the backend using credentials provided via a `.env` file and maintains an authenticated session for all subsequent API calls.

## Available Tools
The following tools, resources, and prompts are exposed by this MCP server:

### Tools

-   **`get_tasks(project_id: Optional[int], assigned_user_id: Optional[int]) -> Dict`**
    -   Retrieves tasks from the backend.
    -   Can be filtered by `project_id`.
    -   If `assigned_user_id` is not provided, it defaults to fetching tasks assigned to the currently authenticated agent.

## Installation and Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd task-tracker-mcp-server-python-fastmcp
    ```

2.  **Create and activate a virtual environment using `uv`:**
    ```bash
    uv venv
    source .venv/bin/activate
    ```

3.  **Install dependencies using `uv`:**
    The project's dependencies are defined in `pyproject.toml` and locked in `uv.lock`. Use `uv sync` to install them.
    ```bash
    uv sync
    ```

4.  **Create a `.env` file:**
    This server loads configuration from a `.env` file in the project root. Create this file and add the necessary credentials:
    ```
    BACKEND_URL="http://your-backend-api-url.com"
    TASKAPP_USER="your-username"
    TASKAPP_PASSWORD="your-password"
    ```

## Testing with MCP Inspector

Once the server is configured, you can test it locally.

1.  **Run the server:**
    ```bash
    uv run mcp run main.py
    ```
    On startup, the server will attempt to log in to the backend. You should see log messages indicating success or failure.

2.  **Use the MCP Inspector:**
    In a separate terminal (with the virtual environment activated), use the `mcp` CLI to inspect the running server and test its tools.
    ```bash
    uv run mcp dev main.py
    ```
    This will open an interactive inspector where you can see available tools and call them. For example, to call the `get_tasks` tool:
    ```
    call get_tasks --params '{"project_id": 1}'
    ```

## Configuration in Zed

To use this MCP server with the Zed editor, you need to configure it in your `settings.json` file.

1.  Open Zed and go to `File > Settings` (or `Cmd + ,`).
2.  Click "Open JSON" to edit the `settings.json` file.
3.  Add the following configuration to the `context_servers` list.

```json
{
"context_servers": {
  "taskapp-mcp-server": {
    "source": "custom",
    "command": "uv",
    "args": [
      "run",
      "--with",
      "mcp,httpx",
      "mcp",
      "run",
      "main.py"
    ],
    "env": {
      "BACKEND_URL": "your_url_to_the_backend",
      "TASKAPP_USER": "your_username",
      "TASKAPP_PASSWORD": "your_password"
    }
  },
```

After saving the settings, Zed will be able to communicate with your MCP server.
