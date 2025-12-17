# MCP Image Generation Agent

This project implements an AI Agent that connects to a Model Context Protocol (MCP) server to generate images. It features a "Human-in-the-loop" approval process for bulk generation requests.

## Architecture

- **Agent (Client):** A CLI application that accepts user prompts and enforces business logic (Approval > 1 image).
- **Server:** An MCP-compliant server that exposes image generation capabilities.

## Usage

1. Install dependencies:
   ```bash
   pip install .
   ```

2. Run the CLI Agent:
   ```bash
   mcp-image-agent generate "a futuristic city with flying cars" --count 1
   ```

3. Run the MCP server (stdio):
   ```bash
   mcp-image-server
   ```

4. Run the Streamlit UI:
   ```bash
   streamlit run src/mcp_image_agent/web_agent.py
   ```
