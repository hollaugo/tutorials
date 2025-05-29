# Financial MCP Server

This project demonstrates how to build and deploy a financial data MCP (Model Context Protocol) server using FastMCP, yfinance, Docker, and Render.

## Features
- Financial data tools (stock summary, earnings, SEC filings, analyst targets, etc.)
- Analyst-focused prompt resources
- Dockerized for easy deployment
- Ready for cloud deployment (e.g., Render)

---

## Step-by-Step: Create and Deploy Your MCP Server

### 1. **Project Setup**

- Create a new directory for your project.
- Initialize a Python virtual environment:
  ```sh
  python -m venv .venv
  source .venv/bin/activate
  ```
- Install dependencies using uv:
  ```sh
  uv pip install yfinance fastmcp requests beautifulsoup4 python-dotenv
  ```
- Freeze dependencies:
  ```sh
  uv pip freeze > requirements.txt
  ```

### 2. **Build Your MCP Server**

- Create `server.py` and implement your tools and prompts using FastMCP and yfinance.
- Example server startup:
  ```python
  import os
  from fastmcp import FastMCP
  # ... your imports and tool definitions ...
  mcp = FastMCP()
  if __name__ == "__main__":
      port = int(os.environ.get("PORT", 8005))
      mcp.run(transport="streamable-http", port=port, host="0.0.0.0")
  ```

### 3. **Prepare for Docker**

- Create a `.dockerignore` file:
  ```
  .venv
  __pycache__
  *.pyc
  *.pyo
  *.pyd
  *.pyz
  *.pyw
  ```
- Create a `Dockerfile`:
  ```dockerfile
  FROM python:3.11-slim
  ENV PYTHONDONTWRITEBYTECODE=1
  ENV PYTHONUNBUFFERED=1
  WORKDIR /app
  RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*
  RUN pip install --upgrade pip && pip install uv
  COPY . /app/
  RUN uv pip install -r requirements.txt --system || true
  ENV PORT=8005
  EXPOSE $PORT
  CMD python server.py
  ```

### 4. **Build and Push Docker Image to Docker Hub**

- Log in to Docker Hub (create an account if you don't have one):
  ```sh
  docker login
  ```
- Build your image for the correct platform:
  ```sh
  docker build --platform=linux/amd64 -t yourusername/your-repo:latest .
  ```
- Push your image:
  ```sh
  docker push yourusername/your-repo:latest
  ```

### 5. **Deploy on Render**

- Go to [Render Web Services](https://render.com/docs/web-services#port-binding)
- Choose "Deploy an existing image from a registry"
- Use your image URL: `yourusername/your-repo:latest`
- Render will automatically set the `PORT` environment variable and expects your service to bind to `0.0.0.0:$PORT`
- Wait for the deployment to complete and test your endpoint

---

## Troubleshooting
- **404 on /**: This is normal unless you serve something at the root path. Your MCP server likely serves at `/mcp` or another path.
- **No open ports detected**: Ensure your server binds to `host="0.0.0.0"` and uses the `PORT` environment variable.
- **Docker build errors**: Make sure `.venv` is in `.dockerignore` and you use `--platform=linux/amd64` for cloud deployment.
- **Docker Hub authentication**: Use your username (not email) and a personal access token if you have 2FA enabled.

---

## References
- [FastMCP Documentation](https://gofastmcp.com/)
- [yfinance Documentation](https://ranaroussi.github.io/yfinance/)
- [Render Web Services Docs](https://render.com/docs/web-services#port-binding)
- [Docker Hub Docs](https://docs.docker.com/docker-hub/)
