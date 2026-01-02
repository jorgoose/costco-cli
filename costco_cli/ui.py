"""Terminal UI components for Costco CLI."""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.spinner import Spinner
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.align import Align
from rich.columns import Columns
from rich import box
import time
import random

console = Console()

# Costco brand colors
COSTCO_RED = "red"
COSTCO_BLUE = "blue"
COSTCO_WHITE = "white"
COSTCO_YELLOW = "yellow"

COSTCO_LOGO = """
[bold red]        @@@@@@@@@@
     @@@@@@@@@@@@@@@
   @@@@@@@@    @@@@@@   @@@@@@@@   @@@@@@@@ @@@@@@@@@@  @@@@@@@@   @@@@@@@@
  @@@@@@@        @@   @@@    @@@  @@@         @@@     @@@    @@@ @@@    @@@
  @@@@@@             @@@@        @@@@@@@@     @@@     @@@        @@@    @@@
  @@@@@@@       @@    @@@    @@@      @@@@    @@@     @@@    @@@ @@@    @@@
   @@@@@@@@@@@@@@@@    @@@@@@@@  @@@@@@@@     @@@      @@@@@@@@   @@@@@@@@[/bold red]

[bold blue]================================================================[/bold blue]
[bold white on red]  *  W H O L E S A L E   T E R M I N A L   A C C E S S  *  [/bold white on red]
[bold blue]================================================================[/bold blue]"""

WAREHOUSE_BANNER = ""

MEMBER_CARD = """[bold yellow]+-------------------------------------+
|  [white]EXECUTIVE MEMBER[/white]  [red]*[/red] [white]CLI ACCESS[/white]    |
|  [dim]---------------------------------[/dim]  |
|  [cyan]Member:[/cyan] [white]Terminal User[/white]              |
|  [cyan]Status:[/cyan] [green]* AUTHENTICATED[/green]            |
+-------------------------------------+[/bold yellow]"""

SHOPPING_CART_ICON = "[bold yellow][CART][/bold yellow]"

# Costco-themed loading messages
COSTCO_LOADING_MESSAGES = [
    "Scanning warehouse aisles...",
    "Checking bulk inventory...",
    "Calculating member savings...",
    "Reviewing Kirkland Signature selection...",
    "Accessing wholesale database...",
    "Checking food court hot dog availability...",
    "Verifying Executive Member benefits...",
    "Inspecting product samples...",
    "Calculating per-unit pricing...",
    "Reviewing member-only deals...",
    "Checking warehouse stock levels...",
    "Scanning membership card...",
]

_loading_message_index = 0

def get_loading_message() -> str:
    """Get the next Costco-themed loading message."""
    global _loading_message_index
    message = COSTCO_LOADING_MESSAGES[_loading_message_index]
    _loading_message_index = (_loading_message_index + 1) % len(COSTCO_LOADING_MESSAGES)
    return message


def clear_screen():
    """Clear the terminal screen."""
    console.clear()


def show_boot_sequence():
    """Display the Costco CLI boot sequence with ASCII art."""
    clear_screen()

    # Display main logo
    console.print()
    console.print(COSTCO_LOGO)
    console.print()

    # Animated boot sequence
    boot_steps = [
        ("Scanning membership barcode", "green", "[OK]"),
        ("Checking food court hot dog supply ($1.50!)", "yellow", "[OK]"),
        ("Loading warehouse inventory", "cyan", "[OK]"),
        ("Verifying rotisserie chicken temperature", "yellow", "[OK]"),
        ("Authenticating Kirkland Signature", "green", "[OK]"),
    ]

    with Progress(
        SpinnerColumn(style="red"),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=20, complete_style="red", finished_style="green"),
        TextColumn("[bold]{task.fields[status]}"),
        console=console,
        transient=True,
    ) as progress:
        for step, color, checkmark in boot_steps:
            task = progress.add_task(step, total=100, status="...")
            for i in range(100):
                time.sleep(0.008)
                progress.update(task, advance=1)
            progress.update(task, status=f"[{color}]{checkmark}[/{color}]")
            time.sleep(0.1)

    # Show completion status
    for step, color, checkmark in boot_steps:
        console.print(f"  [{color}]{checkmark}[/{color}] [dim]{step}[/dim]")

    console.print()
    console.print(MEMBER_CARD)
    console.print()

    # Ready message
    ready_panel = Panel(
        "[bold green]SYSTEM READY[/bold green]\n"
        "[white]Type [bold cyan]help[/bold cyan] for available commands[/white]",
        border_style="green",
        box=box.ROUNDED,
        padding=(0, 2),
    )
    console.print(ready_panel)
    console.print()


def show_command_header(command: str, icon: str = "🛒"):
    """Show a styled header for commands."""
    clear_screen()

    header = Panel(
        f"[bold white]{icon} {command.upper()}[/bold white]",
        style="red",
        box=box.DOUBLE,
        padding=(0, 2),
    )
    console.print(header)
    console.print()


def show_status(message: str, status: str = "info"):
    """Display a status message."""
    icons = {
        "info": "[bold blue][i][/bold blue]",
        "success": "[bold green][+][/bold green]",
        "warning": "[bold yellow][!][/bold yellow]",
        "error": "[bold red][x][/bold red]",
    }
    colors = {
        "info": "blue",
        "success": "green",
        "warning": "yellow",
        "error": "red",
    }
    icon = icons.get(status, "•")
    color = colors.get(status, "white")
    console.print(f" {icon} [{color}]{message}[/{color}]")


def show_thinking(message: str = "Processing your request..."):
    """Show a spinner while the agent is working."""
    return console.status(
        f"[bold red][CART][/bold red] [bold cyan]{message}[/bold cyan]",
        spinner="dots",
        spinner_style="red"
    )


def show_agent_action(action: str, details: str = "", verbose: bool = True):
    """Display an agent action in the terminal."""
    if not verbose:
        return
    console.print(f"  [bold cyan]>[/bold cyan] [white]{action}[/white]")
    if details:
        console.print(f"    [dim]{details}[/dim]")


def show_tool_call(tool_name: str, params: str = "", verbose: bool = True):
    """Display a tool call being made."""
    if not verbose:
        return
    console.print(f"  [bold magenta]>>[/bold magenta] [magenta]{tool_name}[/magenta]")
    if params:
        console.print(f"    [dim]{params}[/dim]")




def show_costco_loading(message: str = None):
    """Show a Costco-themed loading message (single line, no animation)."""
    if message is None:
        message = get_loading_message()
    console.print(f"  [bold blue][CART][/bold blue] [cyan]{message}[/cyan]")


def create_loading_display():
    """Create an animated loading display that updates in place.
    
    Returns a context manager that can be used with 'with' statement.
    Updates the display with rotating messages and animated dots.
    """
    from rich.live import Live
    from rich.text import Text
    import time
    
    class LoadingDisplay:
        def __init__(self):
            self.message_index = 0
            self.dot_count = 0
            self.live = None
            self.last_update = time.time()
            self.message_change_interval = 2.0  # Change message every 2 seconds
            self.dot_interval = 0.5  # Change dots every 0.5 seconds
            
        def __enter__(self):
            from rich.text import Text
            initial_text = Text()
            initial_text.append("  ", style="")
            initial_text.append("[CART]", style="bold blue")
            initial_text.append(" ", style="")
            initial_text.append(COSTCO_LOADING_MESSAGES[0], style="cyan")
            initial_text.append(".", style="cyan")
            
            self.live = Live(initial_text, console=console, refresh_per_second=4)
            self.live.__enter__()
            return self
            
        def __exit__(self, *args):
            if self.live:
                self.live.__exit__(*args)
                
        def update(self):
            """Update the display with new message and/or dots."""
            current_time = time.time()
            
            # Check if we should change the message
            if current_time - self.last_update >= self.message_change_interval:
                self.message_index = (self.message_index + 1) % len(COSTCO_LOADING_MESSAGES)
                self.last_update = current_time
                self.dot_count = 0
            
            # Animate dots (., .., ..., .)
            dots_elapsed = current_time - self.last_update
            self.dot_count = int((dots_elapsed / self.dot_interval) % 4)
            dots = "." * (self.dot_count + 1) if self.dot_count < 3 else "."
            
            # Build the display text
            text = Text()
            text.append("  ", style="")
            text.append("[CART]", style="bold blue")
            text.append(" ", style="")
            text.append(COSTCO_LOADING_MESSAGES[self.message_index], style="cyan")
            text.append(dots + " " * (3 - len(dots)), style="cyan")  # Pad to keep width consistent
            
            if self.live:
                self.live.update(text)
    
    return LoadingDisplay()

def show_search_results(results: list[dict], has_more: bool = False):
    """Display search results in a formatted table."""
    if not results:
        console.print(Panel(
            "[yellow]No products found matching your search.[/yellow]\n"
            "[dim]Try different keywords or check spelling.[/dim]",
            border_style="yellow",
            title="[bold yellow]No Results[/bold yellow]",
        ))
        return

    table = Table(
        title="[bold white on red] SEARCH RESULTS [/bold white on red]",
        show_header=True,
        header_style="bold white on blue",
        border_style="red",
        box=box.ROUNDED,
        padding=(0, 1),
    )
    table.add_column("#", style="bold yellow", width=4, justify="center")
    table.add_column("Product", style="white", min_width=35)
    table.add_column("Price", style="bold green", justify="right", width=12)
    table.add_column("Unit", style="dim cyan", width=15)

    for i, item in enumerate(results, 1):
        price = item.get("price", "N/A")

        # Clean up price display for edge cases
        if price != "N/A":
            price_lower = price.lower()
            # Handle "Warehouse pricing may vary" and similar cases
            if "warehouse" in price_lower or "pricing may vary" in price_lower or "may vary" in price_lower:
                price = "See in-store"
            elif not price.startswith("$"):
                price = f"${price}"

        table.add_row(
            str(i),
            item.get("name", "Unknown"),
            price,
            item.get("unit", ""),
        )

    console.print(table)
    console.print()
    if has_more:
        console.print("[dim]TIP: Use [cyan]add <number>[/cyan] to add items (e.g., add 1) or [cyan]more[/cyan] to see additional results[/dim]")
    else:
        console.print("[dim]TIP: Use [cyan]add <number>[/cyan] to add items to cart (e.g., add 1)[/dim]")


def show_cart(items: list[dict], total: str = ""):
    """Display the current cart contents."""
    if not items:
        empty_cart = Panel(
            "[yellow]Your cart is empty![/yellow]\n\n"
            "[dim]Start shopping with:[/dim]\n"
            "[cyan]  search \"item\"[/cyan]\n"
            "[cyan]  add \"item\"[/cyan]",
            border_style="yellow",
            title="[bold yellow]EMPTY CART[/bold yellow]",
            padding=(1, 2),
        )
        console.print(empty_cart)
        return

    table = Table(
        title="[bold white on red] YOUR CART [/bold white on red]",
        show_header=True,
        header_style="bold white on blue",
        border_style="red",
        box=box.ROUNDED,
        padding=(0, 1),
    )
    table.add_column("Item", style="white", min_width=35)
    table.add_column("Qty", style="bold cyan", justify="center", width=6)
    table.add_column("Price", style="bold green", justify="right", width=12)

    for item in items:
        price = item.get("price", "N/A")

        # Clean up price display for edge cases
        if price != "N/A":
            price_lower = price.lower()
            # Handle "Warehouse pricing may vary" and similar cases
            if "warehouse" in price_lower or "pricing may vary" in price_lower or "may vary" in price_lower:
                price = "See in-store"
            elif not price.startswith("$"):
                price = f"${price}"

        table.add_row(
            item.get("name", "Unknown"),
            str(item.get("quantity", 1)),
            price,
        )

    console.print(table)

    if total:
        if not total.startswith("$"):
            total = f"${total}"
        total_panel = Panel(
            f"[bold white]Estimated Total:[/bold white] [bold green]{total}[/bold green]",
            border_style="green",
            box=box.ROUNDED,
            padding=(0, 2),
        )
        console.print(total_panel)

    console.print()
    console.print("[dim]TIP: Use [cyan]checkout[/cyan] to proceed to payment[/dim]")


def show_checkout_warning():
    """Display checkout safety warning."""
    warning = Panel(
        "[bold yellow]<!> SAFETY CHECKPOINT[/bold yellow]\n"
        "[bold white]-------------------------------------------[/bold white]\n\n"
        "[white]The browser will open to the final checkout page.[/white]\n"
        "[white]Please review your order and [bold]manually click[/bold] 'Place Order'.[/white]\n\n"
        "[dim][SECURE] This CLI will [bold]NEVER[/bold] complete purchases automatically.[/dim]\n"
        "[dim]         Your payment info remains secure in your browser.[/dim]",
        title="[bold red][!] MANUAL CONFIRMATION REQUIRED[/bold red]",
        border_style="yellow",
        box=box.DOUBLE,
        padding=(1, 2),
    )
    console.print(warning)
    console.print()


def show_success_banner(message: str):
    """Show a success message in Costco style."""
    banner = Panel(
        f"[bold green][+] {message}[/bold green]",
        border_style="green",
        box=box.ROUNDED,
        padding=(0, 2),
    )
    console.print(banner)


def show_welcome_tip():
    """Show a random shopping tip."""
    tips = [
        "[TIP] Kirkland Signature products offer premium quality at warehouse prices!",
        "[TIP] Check the Food Court for a $1.50 hot dog combo - best deal since 1985!",
        "[TIP] Members save an average of $1,000+ per year shopping at Costco!",
        "[TIP] Executive Members earn 2% annual reward on qualified purchases!",
        "[TIP] Costco's return policy is legendary - satisfaction guaranteed!",
        "[TIP] With the Costco app, you can check Costco Gas Station prices on your phone!",
    ]
    console.print(f"\n[dim]{random.choice(tips)}[/dim]\n")


def prompt_continue(message: str = "Continue?") -> bool:
    """Ask user to confirm an action."""
    from rich.prompt import Confirm
    return Confirm.ask(f"[bold yellow][?][/bold yellow] {message}")
