import asyncio
import base64
import json
import sys

import streamlit as st
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def _run_async(coro):
    """Run an async coroutine from Streamlit safely."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Streamlit may already have a running loop in some environments.
        new_loop = asyncio.new_event_loop()
        try:
            return new_loop.run_until_complete(coro)
        finally:
            new_loop.close()
    return asyncio.run(coro)


async def call_mcp_server(prompt_text: str, num_images: int, server_script: str) -> list[str]:
    """Connects to the local MCP server and requests image generation."""
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[server_script],
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                tools = await session.list_tools()
                if not any(t.name == "generate_images" for t in tools.tools):
                    st.error("Tool 'generate_images' not found on server.")
                    return []

                with st.spinner(f"Agent is generating {num_images} image(s)..."):
                    result = await session.call_tool(
                        "generate_images",
                        arguments={"prompt": prompt_text, "count": num_images},
                    )
                    images_json = result.content[0].text
                    return json.loads(images_json)
    except Exception as e:
        st.error(f"MCP Connection Error: {e}")
        return []


def main() -> None:
    st.set_page_config(
        page_title="MCP Image Agent",
        page_icon="🎨",
        layout="wide",
    )

    st.markdown(
        """
<style>
    .stButton>button { width: 100%; }
    .status-box { padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; }
</style>
""",
        unsafe_allow_html=True,
    )

    st.title("🎨 AI Image Generation Agent")
    st.markdown(
        "This agent uses the **Model Context Protocol (MCP)** to generate images. Bulk requests (>1) require human approval."
    )

    with st.sidebar:
        st.header("Settings")
        count = st.slider("Number of Images", min_value=1, max_value=10, value=1)
        server_script = st.text_input("Server script path", value="src/mcp_image_agent/server.py")
        st.info("💡 Note: Requests for more than 1 image will trigger the approval workflow.")

    prompt = st.text_area(
        "Enter your image description:",
        height=100,
        placeholder="e.g., A futuristic city with flying cars...",
    )

    if "approval_needed" not in st.session_state:
        st.session_state.approval_needed = False
    if "pending_prompt" not in st.session_state:
        st.session_state.pending_prompt = ""
    if "pending_count" not in st.session_state:
        st.session_state.pending_count = 0
    if "generated_images" not in st.session_state:
        st.session_state.generated_images = []

    col1, _col2 = st.columns([1, 4])
    with col1:
        generate_btn = st.button("Generate", type="primary")

    if generate_btn and prompt:
        if count > 1:
            st.session_state.approval_needed = True
            st.session_state.pending_prompt = prompt
            st.session_state.pending_count = count
        else:
            st.session_state.approval_needed = False
            st.session_state.generated_images = _run_async(call_mcp_server(prompt, count, server_script))

    if st.session_state.approval_needed:
        st.divider()
        st.warning("⚠️ **Approval Required**")
        st.write(f"You requested **{st.session_state.pending_count} images**.")
        st.write(f"**Prompt:** *{st.session_state.pending_prompt}*")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Approve & Generate"):
                st.session_state.generated_images = _run_async(
                    call_mcp_server(
                        st.session_state.pending_prompt,
                        st.session_state.pending_count,
                        server_script,
                    )
                )
                st.session_state.approval_needed = False
                st.rerun()
        with c2:
            if st.button("❌ Reject Request"):
                st.session_state.approval_needed = False
                st.info("Request cancelled.")
                st.rerun()

    if st.session_state.generated_images:
        st.divider()
        st.subheader("Gallery")

        cols = st.columns(3)
        for idx, img_b64 in enumerate(st.session_state.generated_images):
            col = cols[idx % 3]
            with col:
                st.image(
                    base64.b64decode(img_b64),
                    caption=f"Result #{idx + 1}",
                    use_container_width=True,
                )

        if st.button("Clear Gallery"):
            st.session_state.generated_images = []
            st.rerun()


if __name__ == "__main__":
    main()


