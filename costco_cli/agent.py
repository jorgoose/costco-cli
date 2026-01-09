"""Claude + MCP Agent orchestration for Costco shopping."""

import asyncio
import json
import os
import sys
import shutil
import traceback
from typing import Any
from contextlib import asynccontextmanager

from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from costco_cli import ui
from costco_cli import config

# Python 3.11+ has ExceptionGroup built-in
try:
    ExceptionGroup
except NameError:
    # For Python < 3.11, use a simple Exception fallback
    ExceptionGroup = Exception


def get_npx_command() -> str:
    """Get the correct npx command for the current platform."""
    if sys.platform == "win32":
        # On Windows, try npx.cmd first
        npx_cmd = shutil.which("npx.cmd")
        if npx_cmd:
            return npx_cmd
        # Fallback to npx.exe
        npx_exe = shutil.which("npx.exe")
        if npx_exe:
            return npx_exe
        # Last resort
        return "npx.cmd"
    else:
        return "npx"

# System prompt for the shopping assistant
SYSTEM_PROMPT = """You are a helpful Costco shopping assistant integrated with a Playwright browser automation tool.

Your job is to help users:
1. Search for products on Costco.com
2. Add items to their cart
3. View cart contents
4. Navigate to checkout

IMPORTANT RULES:
- Always navigate to costco.com first if not already there
- Use the browser tools to interact with the website
- Extract product names, prices, and relevant details from the page
- When searching, use the Costco search bar
- Be concise in your responses
- Report what you find in a structured way

When you find products, format them as JSON like:
{"products": [{"name": "...", "price": "...", "unit": "...", "image_url": "...", "product_url": "..."}]}
Include the image_url (product thumbnail/image) and product_url (link to product page) for each product.

When viewing cart, format as JSON like:
{"cart": [{"name": "...", "quantity": ..., "price": "..."}], "total": "..."}

NEVER click "Place Order" or complete a purchase automatically. Always stop at checkout review."""


class CostcoAgent:
    """Agent that orchestrates Claude and Playwright MCP for Costco shopping."""

    def __init__(self, chrome_profile_path: str | None = None, verbose: bool = False, headless: bool = True):
        # Get API key from config or environment
        api_key = config.get_api_key()
        self.client = Anthropic(api_key=api_key)
        self.chrome_profile_path = chrome_profile_path
        self.session: ClientSession | None = None
        self.tools: list[dict] = []
        self.conversation_history: list[dict] = []
        self.verbose = verbose
        self.headless = headless
    async def start(self):
        """Start the persistent browser connection."""
        if self.session is not None:
            return  # Already connected
        
        server_params = self._get_server_params()
        
        try:
            # Store the stdio client context managers
            self._stdio_client = stdio_client(server_params)
            self._read_write = await self._stdio_client.__aenter__()
            read, write = self._read_write
            
            # Create and store the session
            self._session_cm = ClientSession(read, write)
            self.session = await self._session_cm.__aenter__()
            
            # Initialize the session
            await self.session.initialize()
            
            # Get available tools
            tools_response = await self.session.list_tools()
            self.tools = [
                {
                    "name": tool.name,
                    "description": tool.description or "",
                    "input_schema": tool.inputSchema,
                }
                for tool in tools_response.tools
            ]
            
            ui.show_status(f"Browser connected with {len(self.tools)} tools", "success")
            
        except ExceptionGroup as eg:
            ui.show_status("Connection error (ExceptionGroup)", "error")
            for i, e in enumerate(eg.exceptions):
                ui.show_status(f"  Sub-error {i+1}: {type(e).__name__}: {e}", "error")
            raise RuntimeError(f"MCP connection failed") from eg
        except Exception as e:
            ui.show_status(f"Connection error: {type(e).__name__}: {e}", "error")
            traceback.print_exc()
            raise
    
    async def stop(self):
        """Stop the persistent browser connection."""
        if self.session is None:
            return  # Not connected
        
        try:
            # Exit the session context manager
            if hasattr(self, '_session_cm'):
                await self._session_cm.__aexit__(None, None, None)
            
            # Exit the stdio client context manager
            if hasattr(self, '_stdio_client'):
                await self._stdio_client.__aexit__(None, None, None)
            
            self.session = None
            ui.show_status("Browser disconnected", "success")
            
        except (Exception, ExceptionGroup) as e:
            # Suppress cleanup errors - they're not critical
            self.session = None
            # Only show error if verbose
            if self.verbose:
                ui.show_status(f"Error during cleanup (non-critical): {e}", "warning")
    
    def is_connected(self) -> bool:
        """Check if the agent is currently connected."""
        return self.session is not None


    def _get_server_params(self) -> StdioServerParameters:
        """Get the MCP server parameters for Playwright."""
        args = ["-y", "@playwright/mcp@latest"]

        # Add headless mode with stealth options to avoid detection
        if self.headless:
            args.append("--headless")
            # Use a realistic user agent to avoid headless detection
            args.extend([
                "--user-agent",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ])
            # Set realistic viewport size
            args.extend(["--viewport-size", "1920x1080"])

        # Add Chrome profile if specified for persistent login
        if self.chrome_profile_path:
            args.extend(["--user-data-dir", self.chrome_profile_path])

        return StdioServerParameters(
            command=get_npx_command(),
            args=args,
        )

    @asynccontextmanager
    async def connect(self):
        """Connect to the Playwright MCP server."""
        server_params = self._get_server_params()

        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    self.session = session

                    # Initialize the session
                    await session.initialize()

                    # Get available tools
                    tools_response = await session.list_tools()
                    self.tools = [
                        {
                            "name": tool.name,
                            "description": tool.description or "",
                            "input_schema": tool.inputSchema,
                        }
                        for tool in tools_response.tools
                    ]

                    ui.show_status(f"Connected with {len(self.tools)} browser tools", "success")

                    try:
                        yield self
                    except Exception as e:
                        ui.show_status(f"Agent error: {e}", "error")
                        raise
                    finally:
                        self.session = None
        except ExceptionGroup as eg:
            # Handle asyncio ExceptionGroup errors
            ui.show_status("Connection error (ExceptionGroup)", "error")
            for i, e in enumerate(eg.exceptions):
                ui.show_status(f"  Sub-error {i+1}: {type(e).__name__}: {e}", "error")
            raise RuntimeError(f"MCP connection failed") from eg
        except Exception as e:
            ui.show_status(f"Connection error: {type(e).__name__}: {e}", "error")
            traceback.print_exc()
            raise

    async def _call_tool(self, tool_name: str, tool_args: dict) -> str:
        """Execute a tool call via MCP."""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")

        ui.show_tool_call(tool_name, json.dumps(tool_args, indent=2)[:100] + "...", verbose=self.verbose)

        result = await self.session.call_tool(tool_name, tool_args)

        # Extract text content from result
        if result.content:
            return "\n".join(
                block.text if hasattr(block, "text") else str(block)
                for block in result.content
            )
        return ""

    async def run(self, user_message: str) -> str:
        """Run the agent loop for a user message."""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")

        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message,
        })

        # Check and compact conversation history if needed
        self._compact_conversation_history(max_tokens=150000)

        # Convert MCP tools to Anthropic format
        anthropic_tools = [
            {
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool["input_schema"],
            }
            for tool in self.tools
        ]

        final_response = ""
        max_iterations = 20  # Safety limit

        # Create animated loading display for non-verbose mode
        loading_display = None if self.verbose else ui.create_loading_display()

        try:
            if loading_display:
                loading_display.__enter__()
                
            for iteration in range(max_iterations):
                try:
                    if self.verbose:
                        ui.show_status(f"Thinking... (step {iteration + 1})", "info")

                    response = self.client.messages.create(
                        model="claude-haiku-4-5-20251001",
                        max_tokens=4096,
                        system=SYSTEM_PROMPT,
                        tools=anthropic_tools,
                        messages=self.conversation_history,
                    )
                except Exception as e:
                    ui.show_status(f"API Error: {e}", "error")
                    raise

                # Process the response
                assistant_content = []
                tool_results = []

                for block in response.content:
                    if block.type == "text":
                        final_response = block.text
                        assistant_content.append({"type": "text", "text": block.text})
                        ui.show_agent_action("Response", block.text[:100] + "..." if len(block.text) > 100 else block.text, verbose=self.verbose)

                    elif block.type == "tool_use":
                        assistant_content.append({
                            "type": "tool_use",
                            "id": block.id,
                            "name": block.name,
                            "input": block.input,
                        })

                        # Execute the tool
                        try:
                            result = await self._call_tool(block.name, block.input)
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result,
                            })
                        except Exception as e:
                            ui.show_status(f"Tool error: {e}", "warning")
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": f"Error: {str(e)}",
                                "is_error": True,
                            })

                # Add assistant response to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": assistant_content,
                })

                # If there were tool calls, add results and continue
                if tool_results:
                    self.conversation_history.append({
                        "role": "user",
                        "content": tool_results,
                    })

                # Check if we should stop
                if response.stop_reason == "end_turn":
                    break

        finally:
            # Clean up loading display
            if loading_display:
                try:
                    loading_display.__exit__(None, None, None)
                except Exception:
                    pass
        
        return final_response

    def reset_conversation(self):
        """Clear conversation history for a fresh start."""
        self.conversation_history = []

    def _estimate_tokens(self) -> int:
        """Rough estimate of token count in conversation history."""
        # Rough estimate: ~4 characters per token
        total_chars = 0
        for message in self.conversation_history:
            if isinstance(message.get("content"), str):
                total_chars += len(message["content"])
            elif isinstance(message.get("content"), list):
                for block in message["content"]:
                    if isinstance(block, dict):
                        if "text" in block:
                            total_chars += len(block["text"])
                        if "content" in block:
                            total_chars += len(str(block["content"]))
        return total_chars // 4

    def _compact_conversation_history(self, max_tokens: int = 150000):
        """Compact conversation history using Claude to summarize when too large.

        Uses Claude to create a summary of the conversation, preserving important context.
        """
        estimated_tokens = self._estimate_tokens()

        if estimated_tokens > max_tokens:
            if self.verbose:
                ui.show_status(f"Compacting conversation history ({estimated_tokens} tokens)...", "info")

            try:
                # Build a summary of the conversation using Claude
                summary_prompt = (
                    "Summarize the following Costco shopping session conversation history. "
                    "Include: what products were searched for, what was added to cart, and current cart state. "
                    "Keep it concise but preserve all important information.\n\n"
                    f"Conversation: {str(self.conversation_history)}"
                )

                # Call Claude to create summary (without tools, just text)
                response = self.client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=2000,
                    messages=[{"role": "user", "content": summary_prompt}]
                )

                summary = response.content[0].text if response.content else "Shopping session in progress."

                # Replace conversation history with summary
                self.conversation_history = [
                    {"role": "user", "content": "Previous session summary: " + summary}
                ]

                if self.verbose:
                    ui.show_status(f"Conversation compacted to {self._estimate_tokens()} tokens", "info")

            except Exception as e:
                # Fallback to simple trimming if compaction fails
                if self.verbose:
                    ui.show_status(f"Compaction failed, trimming instead: {e}", "warning")
                keep_count = max(1, len(self.conversation_history) // 3)
                self.conversation_history = self.conversation_history[-keep_count:]


async def search_products(query: str, chrome_profile: str | None = None, agent: CostcoAgent | None = None) -> list[dict]:
    """Search for products on Costco.com."""
    # Use provided agent or create temporary one
    use_temp_agent = agent is None
    if use_temp_agent:
        agent = CostcoAgent(chrome_profile)

    async def _search(agent):
        response = await agent.run(
            f"Search for '{query}' on Costco.com and return the top results with prices. "
            "Format the results as JSON with products array."
        )

        # Try to extract JSON from response
        try:
            # Look for JSON in the response
            import re
            json_match = re.search(r'\{.*"products".*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return data.get("products", [])
        except (json.JSONDecodeError, AttributeError):
            pass

        return []
    
    if use_temp_agent:
        async with agent.connect():
            return await _search(agent)
    else:
        return await _search(agent)


async def add_to_cart(item: str, chrome_profile: str | None = None, agent: CostcoAgent | None = None) -> bool:
    """Add an item to the cart."""
    use_temp_agent = agent is None
    if use_temp_agent:
        agent = CostcoAgent(chrome_profile)

    async def _add(agent):
        response = await agent.run(
            f"Search for '{item}' on Costco.com, find the best match, and add it to the cart. "
            "Confirm when the item has been added."
        )
        return "added" in response.lower() or "cart" in response.lower()
    
    if use_temp_agent:
        async with agent.connect():
            return await _add(agent)
    else:
        return await _add(agent)

async def add_to_cart_by_product(product: dict, chrome_profile: str | None = None, agent: CostcoAgent | None = None) -> bool:
    """Add a specific product to the cart using product details."""
    use_temp_agent = agent is None
    if use_temp_agent:
        agent = CostcoAgent(chrome_profile)

    product_name = product.get("name", "Unknown")
    product_price = product.get("price", "")

    async def _add(agent):
        response = await agent.run(
            f"Search for '{product_name}' with price '{product_price}' on Costco.com, "
            f"find the exact match, and add it to the cart. "
            "Confirm when the item has been added."
        )
        return "added" in response.lower() or "cart" in response.lower()
    
    if use_temp_agent:
        async with agent.connect():
            return await _add(agent)
    else:
        return await _add(agent)



async def view_cart(chrome_profile: str | None = None, agent: CostcoAgent | None = None) -> tuple[list[dict], str]:
    """View the current cart contents."""
    use_temp_agent = agent is None
    if use_temp_agent:
        agent = CostcoAgent(chrome_profile)

    async def _view(agent):
        response = await agent.run(
            "Navigate to the Costco.com cart page and extract ALL items with their details. "
            "For each item, extract: name (product name), quantity (number of items), and price (item price). "
            "Also get the cart total. "
            "Return ONLY valid JSON in this exact format: "
            '{"cart": [{"name": "Product Name", "quantity": 1, "price": "19.99"}], "total": "19.99"}'
        )

        # Try to extract JSON from response
        try:
            import re
            # Try to find JSON block in the response
            json_match = re.search(r'\{.*?"cart".*?\[.*?\].*?\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                cart_items = data.get("cart", [])

                # Validate that cart items have required fields
                validated_items = []
                for item in cart_items:
                    if isinstance(item, dict) and "name" in item:
                        validated_items.append({
                            "name": item.get("name", "Unknown Product"),
                            "quantity": item.get("quantity", 1),
                            "price": item.get("price", "N/A")
                        })

                return validated_items, data.get("total", "")
        except (json.JSONDecodeError, AttributeError, TypeError) as e:
            ui.show_status(f"Failed to parse cart data: {e}", "warning")

        return [], ""
    
    if use_temp_agent:
        async with agent.connect():
            return await _view(agent)
    else:
        return await _view(agent)


async def goto_checkout(chrome_profile: str | None = None, agent: CostcoAgent | None = None) -> bool:
    """Navigate to checkout page (does NOT complete purchase)."""
    use_temp_agent = agent is None
    if use_temp_agent:
        agent = CostcoAgent(chrome_profile)

    async def _checkout(agent):
        response = await agent.run(
            "Navigate to the Costco.com checkout page. "
            "DO NOT click any 'Place Order' or 'Complete Purchase' buttons. "
            "Just get to the order review page and stop there."
        )
        return "checkout" in response.lower() or "review" in response.lower()
    
    if use_temp_agent:
        async with agent.connect():
            return await _checkout(agent)
    else:
        return await _checkout(agent)


async def login_to_costco(chrome_profile: str | None = None, agent: CostcoAgent | None = None) -> bool:
    """Navigate to Costco login page and wait for user to log in."""
    use_temp_agent = agent is None
    if use_temp_agent:
        agent = CostcoAgent(chrome_profile)

    async def _login(agent):
        response = await agent.run(
            "Navigate to https://www.costco.com/LogonForm. "
            "This is the Costco sign-in page. Tell the user to log in manually in the browser. "
            "After they log in, confirm that login was successful by checking if the page shows "
            "a member name or 'My Account' link. Report whether login appears successful."
        )
        return "success" in response.lower() or "logged in" in response.lower() or "account" in response.lower()
    
    if use_temp_agent:
        async with agent.connect():
            return await _login(agent)
    else:
        return await _login(agent)
