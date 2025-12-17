import base64
import io
import json
import logging
import random
from typing import List

from mcp.server.fastmcp import FastMCP
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# Initialize the FastMCP server
mcp = FastMCP("ImageGen")


def create_mock_image(prompt: str, index: int) -> str:
    """Creates a placeholder image and returns it as a base64 string."""
    width, height = 512, 512
    color = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))

    img = Image.new("RGB", (width, height), color=color)
    d = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except IOError:
        font = ImageFont.load_default()

    text = f"Image #{index}\nPrompt: {prompt[:30]}..."
    d.text((50, 200), text, fill=(255, 255, 255), font=font)

    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()


@mcp.tool()
def generate_images(prompt: str, count: int = 1) -> str:
    """
    Generates images based on a text prompt.
    Returns a JSON string of base64 encoded images.
    """
    if count < 1:
        raise ValueError("count must be >= 1")

    logger.info("Received request to generate %s images for %r", count, prompt)

    images: List[str] = []
    for i in range(count):
        images.append(create_mock_image(prompt, i + 1))

    return json.dumps(images)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    mcp.run()


if __name__ == "__main__":
    main()


