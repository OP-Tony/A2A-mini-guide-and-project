import asyncio
import sys

import typer
from rich.console import Console
from rich.prompt import Confirm

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

app = typer.Typer(add_completion=False)
console = Console()


async def run_agent(prompt: str, count: int, server_script: str) -> None:
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[server_script],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            tool_name = "generate_images"

            if not any(t.name == tool_name for t in tools.tools):
                console.print(f"[bold red]Error:[/bold red] Tool '{tool_name}' not found on server.")
                return

            if count > 1:
                console.print(
                    f"[bold yellow]⚠️  Bulk Request Detected:[/bold yellow] You are asking for {count} images."
                )
                console.print(f"Prompt: [italic]'{prompt}'[/italic]")
                if not Confirm.ask("Do you approve this generation cost?"):
                    console.print("[bold red]Request Cancelled by User.[/bold red]")
                    return
                console.print("[bold green]Request Approved.[/bold green]")
            else:
                console.print("[blue]Single image request. Auto-approving...[/blue]")

            console.print(f"[dim]Calling MCP Tool: {tool_name}...[/dim]")
            try:
                result = await session.call_tool(tool_name, arguments={"prompt": prompt, "count": count})

                for content in result.content:
                    if content.type == "text":
                        console.print(f"[bold green]Result:[/bold green] {content.text}")
                    else:
                        console.print(f"[bold green]Result (Type: {content.type}):[/bold green] {content}")
            except Exception as e:
                console.print(f"[bold red]Error executing tool:[/bold red] {e}")


@app.command()
def generate(
    prompt: str = typer.Argument(..., help="The description of the image to generate"),
    count: int = typer.Option(1, "--count", "-c", help="Number of images to generate"),
    server_script: str = typer.Option(
        "src/mcp_image_agent/server.py",
        "--server-script",
        help="Path to the MCP server script to spawn (stdio transport).",
    ),
) -> None:
    """Generates images using the MCP Agent."""
    asyncio.run(run_agent(prompt, count, server_script))


def main() -> None:
    app()


if __name__ == "__main__":
    main()


