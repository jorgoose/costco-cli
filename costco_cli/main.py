"""Costco CLI - Main entry point."""

import asyncio
import os
import sys
import warnings
from typing import Optional

import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich import box

from costco_cli import ui
from costco_cli import agent
from costco_cli import config

app = typer.Typer(
    name="costco",
    help="AI-powered shopping assistant for Costco.com",
    add_completion=False,
)
console = Console()

# Default Chrome profile path (can be overridden via env var)
DEFAULT_CHROME_PROFILE = os.environ.get(
    "COSTCO_CHROME_PROFILE",
    os.path.expanduser("~/.costco-cli/chrome-profile")
)


# Session state to track search results
class SessionState:
    """Tracks the current session state for search results."""
    def __init__(self):
        self.search_results: list[dict] = []
        self.current_page: int = 0
        self.page_size: int = 5
        self.last_query: str = ""
        self.verbose_mode: bool = False  # Show agent details when True

    def has_results(self) -> bool:
        """Check if there are any search results."""
        return len(self.search_results) > 0

    def get_current_page_results(self) -> list[dict]:
        """Get results for the current page."""
        start = self.current_page * self.page_size
        end = start + self.page_size
        return self.search_results[start:end]

    def has_next_page(self) -> bool:
        """Check if there are more results to show."""
        return (self.current_page + 1) * self.page_size < len(self.search_results)

    def next_page(self) -> bool:
        """Move to the next page. Returns True if successful."""
        if self.has_next_page():
            self.current_page += 1
            return True
        return False

    def reset(self):
        """Clear all session state."""
        self.search_results = []
        self.current_page = 0
        self.last_query = ""


# Global session instance
session = SessionState()

def _suppress_asyncio_cleanup_errors():
    """Suppress asyncio cleanup error output."""
    import sys
    
    # Save original stderr
    original_stderr = sys.stderr
    
    class SuppressCleanupErrors:
        def __init__(self):
            self.original = original_stderr
            self.suppressing = False
            
        def write(self, text):
            # Check if this is a cleanup error we want to suppress
            if any(pattern in text.lower() for pattern in [
                'cancel scope',
                'unhandled exception during asyncio.run() shutdown',
                'task finished',
                'exception group',
                'generatorexit'
            ]):
                self.suppressing = True
                return
            
            # If we started suppressing, continue until we see a non-error line
            if self.suppressing:
                if text.strip() and not text.startswith(' '):
                    self.suppressing = False
                else:
                    return
                    
            self.original.write(text)
            
        def flush(self):
            self.original.flush()
    
    sys.stderr = SuppressCleanupErrors()




def get_chrome_profile() -> str:
    """Get the Chrome profile path, creating if needed."""
    profile = os.environ.get("COSTCO_CHROME_PROFILE", DEFAULT_CHROME_PROFILE)
    # Always return the profile path - it will be created when needed
    os.makedirs(profile, exist_ok=True)
    return profile


def show_help_menu():
    """Display the interactive help menu."""
    help_text = """
[bold white]Shopping Commands:[/bold white]
  [bold cyan]search[/bold cyan] [dim]<query>[/dim]     Search for products
  [bold cyan]add[/bold cyan] [dim]<number>[/dim]       Add item from search results to cart
  [bold cyan]view[/bold cyan] [dim]<number>[/dim]      View product image/page in browser
  [bold cyan]more[/bold cyan]              Show more search results
  [bold cyan]cart[/bold cyan]              View your cart
  [bold cyan]checkout[/bold cyan]          Go to checkout

[bold white]Account Commands:[/bold white]
  [bold cyan]login[/bold cyan]             Sign in to your Costco account
  [bold cyan]apikey[/bold cyan]            Set your Anthropic API key

[bold white]Other Commands:[/bold white]
  [bold cyan]clear[/bold cyan]             Clear the screen
  [bold cyan]verbose[/bold cyan]           Toggle detailed agent output
  [bold cyan]help[/bold cyan]              Show this menu
  [bold cyan]exit[/bold cyan] / [bold cyan]quit[/bold cyan]       Exit Costco CLI

[dim]Example: search kirkland coffee[/dim]
[dim]First time? Run 'apikey' to set up, then 'login' to sign in![/dim]
"""
    console.print(Panel(
        help_text,
        title="[bold red]COSTCO CLI HELP[/bold red]",
        border_style="blue",
        box=box.ROUNDED,
        padding=(0, 2),
    ))


async def handle_search(query: str, persistent_agent=None):
    """Handle search command."""
    import traceback

    if not query:
        ui.show_status("Please provide a search query", "warning")
        console.print("[dim]Example: search kirkland coffee[/dim]")
        return

    ui.show_status(f"Searching for: {query}", "info")
    console.print()

    try:
        results = await agent.search_products(query, get_chrome_profile(), agent=persistent_agent)

        if results:
            # Store all results in session
            session.search_results = results
            session.current_page = 0
            session.last_query = query

            # Display first page
            page_results = session.get_current_page_results()
            ui.show_search_results(page_results, session.has_next_page())
        else:
            ui.show_status("No products found or could not parse results.", "warning")
            console.print("[dim]The agent may have found results but couldn't format them.[/dim]")
            session.reset()
    except Exception as e:
        ui.show_status(f"Error: {e}", "error")
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        session.reset()



async def handle_more():
    """Handle showing more search results."""
    if not session.has_results():
        ui.show_status("No search results available. Please search first.", "warning")
        console.print("[dim]Example: search kirkland coffee[/dim]")
        return

    if not session.has_next_page():
        ui.show_status("No more results to show.", "info")
        return

    # Move to next page
    session.next_page()
    page_results = session.get_current_page_results()

    console.print(f"\n[bold cyan]Showing page {session.current_page + 1} of search results for:[/bold cyan] [white]{session.last_query}[/white]\n")
    ui.show_search_results(page_results, session.has_next_page())



async def handle_view(item: str):
    """Handle viewing product image/page in browser."""
    import webbrowser
    
    if not item:
        if session.has_results():
            ui.show_status("Please specify an item number to view", "warning")
            console.print("[dim]Example: view 1[/dim]")
        else:
            ui.show_status("Please search for products first.", "warning")
            console.print("[dim]Example: search kirkland coffee[/dim]")
        return

    # Check if a search has been performed
    if not session.has_results():
        ui.show_status("Please search for products first.", "warning")
        console.print("[dim]Example: search kirkland coffee[/dim]")
        console.print("[dim]Then use: view <number>[/dim]")
        return

    # Check if item is a number (index into search results)
    if item.isdigit():
        item_index = int(item) - 1  # Convert to 0-indexed

        if 0 <= item_index < len(session.search_results):
            selected_item = session.search_results[item_index]
            product_name = selected_item.get('name', 'Unknown')
            
            # Try to open image URL first, then product URL, then show error
            image_url = selected_item.get('image_url')
            product_url = selected_item.get('product_url')
            
            if image_url:
                ui.show_status(f"Opening image for: {product_name}", "info")
                webbrowser.open(image_url)
                console.print("[dim]Image opened in your browser[/dim]")
            elif product_url:
                ui.show_status(f"Opening product page for: {product_name}", "info")
                webbrowser.open(product_url)
                console.print("[dim]Product page opened in your browser[/dim]")
            else:
                ui.show_status("No image or product URL available for this item", "warning")
        else:
            ui.show_status(f"Invalid item number. Please choose 1-{len(session.search_results)}", "warning")
    else:
        # User provided text instead of number
        ui.show_status("Please use the item number from search results.", "warning")
        console.print("[dim]Example: view 1[/dim]")


async def handle_add(item: str, persistent_agent=None):
    """Handle add to cart command."""
    if not item:
        if session.has_results():
            ui.show_status("Please specify an item number to add", "warning")
            console.print("[dim]Example: add 1[/dim]")
        else:
            ui.show_status("Please search for products first.", "warning")
            console.print("[dim]Example: search kirkland coffee[/dim]")
        return

    # Check if a search has been performed
    if not session.has_results():
        ui.show_status("Please search for products first.", "warning")
        console.print("[dim]Example: search kirkland coffee[/dim]")
        console.print("[dim]Then use: add <number>[/dim]")
        return

    # Check if item is a number (index into search results)
    if item.isdigit():
        item_index = int(item) - 1  # Convert to 0-indexed

        if 0 <= item_index < len(session.search_results):
            selected_item = session.search_results[item_index]

            ui.show_status(f"Adding to cart: {selected_item.get('name', 'Unknown')}", "info")
            console.print()

            try:
                # Pass the full product dict to agent for better targeting
                success = await agent.add_to_cart_by_product(selected_item, get_chrome_profile(), agent=persistent_agent)

                if success:
                    ui.show_success_banner(f"'{selected_item.get('name', 'Unknown')}' added to cart!")
                else:
                    ui.show_status("Could not confirm item was added.", "warning")
            except Exception as e:
                ui.show_status(f"Error: {e}", "error")
        else:
            ui.show_status(f"Invalid item number. Please choose 1-{len(session.search_results)}", "warning")
    else:
        # User provided text instead of number
        ui.show_status("Please use the item number from search results.", "warning")
        console.print("[dim]Example: add 1[/dim]")
        console.print("[dim]Use 'more' to see additional search results[/dim]")


async def handle_cart(persistent_agent=None):
    """Handle view cart command."""
    ui.show_status("Fetching cart contents...", "info")
    console.print()

    try:
        items, total = await agent.view_cart(get_chrome_profile(), agent=persistent_agent)
        ui.show_cart(items, total)
    except Exception as e:
        ui.show_status(f"Error: {e}", "error")


async def handle_checkout(persistent_agent=None):
    """Handle checkout command."""
    ui.show_checkout_warning()

    if not ui.prompt_continue("Proceed to checkout page?"):
        ui.show_status("Checkout cancelled.", "info")
        return

    ui.show_status("Navigating to checkout...", "info")
    console.print()

    try:
        success = await agent.goto_checkout(get_chrome_profile(), agent=persistent_agent)

        if success:
            ui.show_success_banner("You are now at the checkout page!")
            console.print("\n[bold yellow]Please review your order in the browser and manually complete the purchase.[/bold yellow]\n")
        else:
            ui.show_status("Could not navigate to checkout.", "warning")
    except Exception as e:
        ui.show_status(f"Error: {e}", "error")


async def handle_login(persistent_agent=None):
    """Handle login command."""
    import traceback

    # Ensure profile directory exists
    os.makedirs(DEFAULT_CHROME_PROFILE, exist_ok=True)

    login_panel = Panel(
        "[bold white]Costco Account Login[/bold white]\n\n"
        "A browser window will open to the Costco sign-in page.\n"
        "[bold yellow]Please log in with your Costco credentials.[/bold yellow]\n\n"
        "Your session will be saved for future commands.\n"
        "[dim]This allows access to member-only prices and items.[/dim]",
        title="[bold red]LOGIN[/bold red]",
        border_style="blue",
        box=box.ROUNDED,
        padding=(1, 2),
    )
    console.print(login_panel)
    console.print()

    if not ui.prompt_continue("Open browser to sign in?"):
        ui.show_status("Login cancelled.", "info")
        return

    ui.show_status("Opening Costco sign-in page...", "info")
    console.print()
    console.print("[bold yellow]Please sign in to your Costco account in the browser window.[/bold yellow]")
    console.print("[dim]The CLI will wait for you to complete the login...[/dim]")
    console.print()

    try:
        success = await agent.login_to_costco(DEFAULT_CHROME_PROFILE, agent=persistent_agent)

        if success:
            ui.show_success_banner("Login successful! Your session has been saved.")
            console.print("[dim]You can now access member-only items and prices.[/dim]")
        else:
            ui.show_status("Could not confirm login status.", "warning")
            console.print("[dim]If you logged in, your session should still be saved.[/dim]")
    except Exception as e:
        ui.show_status(f"Error: {e}", "error")
        console.print(f"[dim]{traceback.format_exc()}[/dim]")


def check_api_key() -> bool:
    """Check if API key is configured."""
    if not config.get_api_key():
        console.print(Panel(
            "[bold red]API Key not configured![/bold red]\n\n"
            "This CLI requires an Anthropic API key to work.\n\n"
            "[bold white]To fix, run:[/bold white]\n"
            "  [bold cyan]apikey[/bold cyan]\n\n"
            "[dim]Get your API key at: https://console.anthropic.com/[/dim]",
            title="[bold red]Missing API Key[/bold red]",
            border_style="red",
            box=box.DOUBLE,
            padding=(1, 2),
        ))
        return False
    return True


def handle_apikey():
    """Handle setting the API key."""
    current_key = config.get_api_key()

    if current_key:
        masked_key = current_key[:10] + "..." + current_key[-4:] if len(current_key) > 14 else "****"
        console.print(f"[dim]Current API key: {masked_key}[/dim]")

    console.print(Panel(
        "[bold white]Set your Anthropic API Key[/bold white]\n\n"
        "Your API key will be saved locally and used for all commands.\n"
        "[dim]Get your key at: https://console.anthropic.com/[/dim]",
        title="[bold red]API KEY SETUP[/bold red]",
        border_style="blue",
        box=box.ROUNDED,
        padding=(1, 2),
    ))
    console.print()

    api_key = Prompt.ask("[bold cyan]Enter your Anthropic API key[/bold cyan]", password=True)

    if api_key and api_key.strip():
        config.set_api_key(api_key.strip())
        ui.show_success_banner("API key saved successfully!")
        console.print(f"[dim]Saved to: {config.CONFIG_FILE}[/dim]")
    else:
        ui.show_status("No API key entered.", "warning")


async def run_interactive():
    """Run the interactive CLI loop."""
    ui.show_boot_sequence()

    # Show API key warning if not set, but don't exit
    if not config.get_api_key():
        console.print("[bold yellow][!] API key not set. Run 'apikey' to configure.[/bold yellow]\n")
    else:
        ui.show_welcome_tip()

    # Create persistent agent (will connect on first use)
    persistent_agent = None

    async def ensure_agent_connected():
        """Ensure the persistent agent is connected (lazy initialization)."""
        nonlocal persistent_agent
        if persistent_agent is None:
            persistent_agent = agent.CostcoAgent(get_chrome_profile(), verbose=session.verbose_mode)
        if not persistent_agent.is_connected():
            await persistent_agent.start()
        return persistent_agent

    while True:
        try:
            # Custom prompt
            console.print("[bold red]Costco CLI[/bold red] [bold blue]>[/bold blue] ", end="")
            user_input = input().strip()

            if not user_input:
                continue

            # Parse command
            parts = user_input.split(maxsplit=1)
            command = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""

            # Handle commands
            if command in ("exit", "quit", "q"):
                # Cleanup persistent agent if connected
                if persistent_agent and persistent_agent.is_connected():
                    console.print()
                    ui.show_status("Closing browser...", "info")
                    try:
                        await persistent_agent.stop()
                    except Exception:
                        pass  # Suppress cleanup errors
                console.print("\n[bold yellow]Thanks for shopping at Costco![/bold yellow]")
                console.print("[dim]Come back soon for more warehouse savings![/dim]\n")
                break

            elif command == "help":
                show_help_menu()

            elif command == "clear":
                ui.clear_screen()
                console.print("[bold red]COSTCO CLI[/bold red] [dim]- Type 'help' for commands[/dim]\n")

            elif command == "search":
                if not check_api_key():
                    console.print()
                    continue
                await handle_search(args, await ensure_agent_connected())
                console.print()

            elif command == "more":
                if not check_api_key():
                    console.print()
                    continue
                await handle_more()
                console.print()

            elif command == "view":
                await handle_view(args)
                console.print()

            elif command == "add":
                if not check_api_key():
                    console.print()
                    continue
                await handle_add(args, await ensure_agent_connected())
                console.print()

            elif command == "cart":
                if not check_api_key():
                    console.print()
                    continue
                await handle_cart(await ensure_agent_connected())
                console.print()

            elif command == "checkout":
                if not check_api_key():
                    console.print()
                    continue
                await handle_checkout(await ensure_agent_connected())
                console.print()

            elif command == "login":
                if not check_api_key():
                    console.print()
                    continue
                await handle_login(await ensure_agent_connected())
                console.print()

            elif command == "apikey":
                handle_apikey()
                console.print()

            elif command == "verbose":
                session.verbose_mode = not session.verbose_mode
                # Update existing agent's verbose flag if it exists
                if persistent_agent:
                    persistent_agent.verbose = session.verbose_mode
                status = "enabled" if session.verbose_mode else "disabled"
                ui.show_status(f"Verbose mode {status}", "success")
                console.print()

            elif command == "setup":
                handle_setup()
                console.print()

            else:
                ui.show_status(f"Unknown command: {command}", "warning")
                console.print("[dim]Type 'help' for available commands[/dim]\n")

        except KeyboardInterrupt:
            console.print("\n")
            ui.show_status("Use 'exit' to quit", "info")
            continue
        except EOFError:
            # Cleanup persistent agent if connected
            if persistent_agent and persistent_agent.is_connected():
                try:
                    await persistent_agent.stop()
                except Exception:
                    pass  # Suppress cleanup errors
            console.print("\n[bold yellow]Goodbye![/bold yellow]\n")
            break



def handle_setup():
    """Handle the setup command."""
    console.print()
    setup_panel = Panel(
        "[bold white]Chrome Profile Setup[/bold white]\n\n"
        "To avoid logging in every time, set up a persistent Chrome profile:\n\n"
        "[cyan]1.[/cyan] Run any command (e.g., [bold]search test[/bold])\n"
        "[cyan]2.[/cyan] Log in to Costco in the browser that opens\n"
        "[cyan]3.[/cyan] Your session will be remembered for future use\n\n"
        f"[dim]Profile location: {DEFAULT_CHROME_PROFILE}[/dim]",
        title="[bold red]SETUP[/bold red]",
        border_style="blue",
        box=box.ROUNDED,
        padding=(1, 2),
    )
    console.print(setup_panel)

    if ui.prompt_continue("Create profile directory now?"):
        os.makedirs(DEFAULT_CHROME_PROFILE, exist_ok=True)
        ui.show_success_banner(f"Profile directory created!")
        console.print(f"[dim]Location: {DEFAULT_CHROME_PROFILE}[/dim]")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Costco CLI - Your AI Shopping Assistant"""
    if ctx.invoked_subcommand is None:
        # Suppress asyncio cleanup warnings and errors
        warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*was never awaited.*")
        warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*coroutine.*")
        _suppress_asyncio_cleanup_errors()
        
        # Launch interactive mode
        try:
            asyncio.run(run_interactive())
        except KeyboardInterrupt:
            # User pressed Ctrl+C - exit cleanly (already handled in run_interactive)
            pass
        except (RuntimeError, ExceptionGroup) as e:
            # Suppress asyncio cleanup errors during shutdown
            if "cancel scope" not in str(e).lower():
                raise  # Re-raise if it's not the cleanup error


@app.command()
def search(
    query: str = typer.Argument(..., help="Product to search for"),
    limit: int = typer.Option(5, "--limit", "-l", help="Max results to show"),
):
    """Search for products on Costco.com."""
    ui.show_boot_sequence()
    asyncio.run(handle_search(query))


@app.command()
def add(
    item: str = typer.Argument(..., help="Item name to add to cart"),
):
    """Add an item to your Costco cart."""
    ui.show_boot_sequence()
    asyncio.run(handle_add(item))


@app.command()
def cart():
    """View your current Costco cart."""
    ui.show_boot_sequence()
    asyncio.run(handle_cart())


@app.command()
def checkout():
    """Navigate to checkout (requires manual confirmation to place order)."""
    ui.show_boot_sequence()
    asyncio.run(handle_checkout())


@app.command()
def login():
    """Sign in to your Costco account."""
    ui.show_boot_sequence()
    asyncio.run(handle_login())


@app.command()
def setup():
    """Set up Chrome profile for persistent Costco login."""
    ui.show_boot_sequence()
    handle_setup()


@app.command()
def version():
    """Show version information."""
    from costco_cli import __version__
    console.print(f"[bold red]Costco CLI[/bold red] v{__version__}")


if __name__ == "__main__":
    app()
