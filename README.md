# Costco CLI

An AI-powered terminal shopping assistant for Costco.com that combines Claude's intelligence with browser automation through the Model Context Protocol (MCP).

## What This Tool Does

Costco CLI is an interactive command-line interface that lets you shop on Costco.com using natural language. Simply type what you want to search for, and Claude will:
- Search Costco.com and extract product information
- Add items to your cart by number from search results
- View your cart contents with pricing
- Navigate to checkout (with human-in-the-loop safety - never auto-purchases)

All interaction happens in your terminal with a Costco-themed interface, while Claude controls a browser in the background via MCP.

## Technologies Used

### Claude API (Anthropic)
This project uses **Claude Haiku 4.5** (released December 2024) via the [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python). Claude acts as the intelligent orchestrator that:
- Interprets user commands
- Plans browser interactions
- Extracts structured product data from web pages
- Manages conversational context across shopping sessions

### Model Context Protocol (MCP)
**MCP** is an open protocol released by Anthropic in November 2024 that standardizes how AI models connect to external tools and data sources. Think of it as "USB for AI" - a universal way to give Claude access to tools like browsers, databases, and APIs.

In this project, MCP enables Claude to:
- Control a Playwright browser instance
- Navigate websites
- Click elements and fill forms
- Extract page content

**Learn more:** https://modelcontextprotocol.io

### Playwright MCP Server
The [Playwright MCP Server](https://github.com/anthropics/mcp-servers/tree/main/playwright) is an official MCP implementation that exposes browser automation capabilities. It runs as a subprocess and communicates with Claude via MCP's JSON-RPC protocol.

## Features

### Core Shopping Functions
- **Search Products** - Find items on Costco.com with prices, images, and descriptions
- **Paginated Results** - Browse through multiple pages of search results
- **Add by Number** - Select items from search results by number (1, 2, 3...)
- **View Cart** - See current cart with quantities and estimated total
- **Product Images** - Open product images and pages in your browser
- **Checkout Navigation** - Go to checkout page safely (manual confirmation required)

### User Experience
- **Costco-Themed UI** - Rich terminal interface with Costco branding and colors
- **Animated Loading** - Fun Costco-themed loading messages with spinner ("Scanning warehouse aisles... |")
- **Headless Browser** - Browser runs invisibly in the background (no windows popping up)
- **Persistent Browser** - Browser stays open between commands for faster interactions
- **Verbose Mode** - Toggle technical details on/off with `verbose` command
- **Chrome Profile Support** - Use a persistent Chrome profile to stay logged in

### Safety Features
- **No Auto-Purchase** - Will NEVER click "Place Order" automatically
- **Human-in-the-Loop** - Checkout stops at review page for manual confirmation
- **Transparent Operations** - Can see all browser actions in verbose mode

## Installation

### Prerequisites
- Python 3.10 or higher
- Node.js and npm (for Playwright MCP server)
- An Anthropic API key ([get one here](https://console.anthropic.com/))

### Setup Steps

```bash
# Clone the repository
git clone https://github.com/yourusername/costco-cli.git
cd costco-cli

# Install the CLI package in editable mode
pip install -e .

# This creates the 'costco' command that you can run from anywhere

# Set your API key (add to ~/.bashrc or ~/.zshrc for persistence)
export ANTHROPIC_API_KEY="your-api-key-here"

# Test the installation
costco --help
```

**Note:** The Playwright MCP server will be installed automatically via `npx` when you first run the CLI.

## Usage

### Interactive Mode (Default)

Start the interactive shopping assistant by simply running:

```bash
costco
```

By default, the browser runs in headless mode (invisible). To see the browser window for debugging:

```bash
costco --show-browser
```

This opens a persistent session where you can use commands:

```
Costco CLI > search chips
[Shows search results with numbers]

Costco CLI > add 1
[Adds item #1 from search results to cart]

Costco CLI > more
[Shows next page of search results]

Costco CLI > cart
[Displays cart contents]

Costco CLI > view 2
[Opens product #2 image/page in browser]

Costco CLI > checkout
[Navigates to checkout page]

Costco CLI > verbose
[Toggles technical details on/off]

Costco CLI > help
[Shows available commands]

Costco CLI > exit
```

### One-Shot Commands

Or use individual commands directly:

```bash
# Search for products
costco search "kirkland coffee"

# Add item to cart
costco add "Kirkland Signature Colombian Coffee"

# View cart
costco cart

# Go to checkout
costco checkout

# Set up persistent Chrome profile (stay logged in)
costco setup
```

### Chrome Profile Setup

To avoid logging in repeatedly, set up a persistent Chrome profile:

```bash
# Run setup wizard
costco setup

# Or set manually
export COSTCO_CHROME_PROFILE="/path/to/chrome/profile"
```

The browser will remember your Costco login across sessions.

## Configuration

### Environment Variables

- `ANTHROPIC_API_KEY` - Your Anthropic API key (required)
- `COSTCO_CHROME_PROFILE` - Path to Chrome profile directory for persistent login (optional)

### Config File

Settings are stored in `~/.costco/config.json`:

```json
{
  "api_key": "your-api-key",
  "chrome_profile_path": "/path/to/chrome/profile"
}
```

## How It Works

```
┌─────────────┐
│   Terminal  │  User types commands
│   (Rich UI) │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│   Costco CLI Host   │  Python + Typer
│   (costco_cli/)     │  Manages session state
└──────┬──────────────┘
       │
       ▼
┌─────────────────────────┐
│   Claude Haiku 4.5      │  Anthropic API
│   (Orchestrator)        │  Plans & executes actions
└──────┬──────────────────┘
       │
       │ MCP Protocol (JSON-RPC)
       ▼
┌─────────────────────────┐
│  Playwright MCP Server  │  Browser automation
│  (npx subprocess)       │  Interacts with Costco.com
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│   Chromium Browser      │  Loads Costco.com
│   (Headless Mode)       │  Performs actions
└─────────────────────────┘
```

**Flow:**
1. User types a command (e.g., "search chips")
2. CLI sends request to Claude via Anthropic API
3. Claude decides which MCP tools to use (navigate, click, extract)
4. MCP server executes browser automation in Playwright
5. Results flow back through the chain to the terminal UI

## Architecture

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **UI** | Rich (Python) | Terminal interface with colors, tables, animations |
| **CLI Framework** | Typer | Command parsing and argument handling |
| **Orchestration** | Claude Haiku 4.5 | Intelligent decision-making and planning |
| **API Client** | Anthropic Python SDK | Communication with Claude |
| **Protocol** | MCP (Model Context Protocol) | Standardized tool integration |
| **Automation** | Playwright MCP Server | Browser control (navigate, click, extract) |
| **Browser** | Chromium (via Playwright) | Renders Costco.com |

## Project Structure

```
costco-cli/
├── costco_cli/
│   ├── __init__.py
│   ├── main.py         # CLI commands & interactive loop
│   ├── agent.py        # Claude + MCP orchestration
│   ├── ui.py           # Terminal UI components
│   └── config.py       # Configuration management
├── pyproject.toml      # Python package configuration
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Safety & Privacy

### Purchase Safety
- The CLI **never** completes purchases automatically
- The `checkout` command stops at the order review page
- You must manually click "Place Order" in the browser
- This is enforced in the system prompt and cannot be overridden

### Data Privacy
- Your Costco credentials are only stored in the Chrome profile (if you set one up)
- API calls to Claude include:
  - Your search queries
  - Product names and prices extracted from pages
  - Your commands and conversation history
- No payment information is sent to Claude
- Browser automation runs locally on your machine

### API Costs
Claude Haiku is very affordable:
- Input: $0.80 per million tokens
- Output: $4.00 per million tokens

A typical shopping session (5-10 searches, adding items, viewing cart) costs approximately **$0.01-0.05**.

## Troubleshooting

### "Connection error: MCP connection failed"
- Ensure Node.js is installed: `node --version`
- Try running npx manually: `npx @playwright/mcp@latest`
- Check that port isn't blocked by firewall

### "API Error: authentication_error"
- Verify your API key is set: `echo $ANTHROPIC_API_KEY`
- Get a new key from https://console.anthropic.com/

### Browser doesn't open / can't see browser
- This is expected! The browser runs in headless mode (invisible in the background)
- You won't see any browser windows - all output appears in the terminal
- To see the browser for debugging, use: `costco --show-browser`
- Playwright will install Chromium automatically on first run
- If the browser automation fails, try: `npx playwright install chromium`

### "Warehouse pricing may vary" shows in results
- This is expected for some products - pricing is only available in-store
- The CLI will display these as "See in-store"

## Development

### Running from Source

```bash
# Clone and install in development mode
git clone https://github.com/yourusername/costco-cli.git
cd costco-cli
pip install -e .

# Run directly (launches interactive mode)
python -m costco_cli.main
```

### Adding New Commands

Edit `costco_cli/main.py` to add new commands to the interactive loop or Typer CLI.

### Modifying the Agent

The agent behavior is controlled by:
- `SYSTEM_PROMPT` in `costco_cli/agent.py` - Claude's instructions
- `run()` method - The agentic loop that calls Claude and executes tools

## Limitations

- Only works with Costco.com (US website)
- Requires Costco membership to add items and checkout
- Some products have warehouse-only pricing
- Browser automation can break if Costco redesigns their website
- Rate limited by Costco's website (please be respectful)

## Future Ideas

- Support for other retailers (Sam's Club, BJ's Wholesale)
- Voice input for hands-free shopping
- Shopping list management
- Price tracking and alerts
- Recipe suggestions with automatic cart filling
- Integration with Costco app features (gas prices, warehouse hours)

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Built with [Claude](https://www.anthropic.com/claude) by Anthropic
- Uses [Model Context Protocol (MCP)](https://modelcontextprotocol.io)
- Browser automation via [Playwright](https://playwright.dev/)
- Terminal UI powered by [Rich](https://github.com/Textualize/rich)
- CLI framework by [Typer](https://typer.tiangolo.com/)

## Learn More

- **Anthropic API Docs:** https://docs.anthropic.com/
- **MCP Documentation:** https://modelcontextprotocol.io/docs
- **Playwright MCP Server:** https://github.com/anthropics/mcp-servers
- **Building with MCP:** https://www.anthropic.com/news/model-context-protocol

---

**Disclaimer:** This is an unofficial tool and is not affiliated with or endorsed by Costco Wholesale Corporation.
