# Costco CLI

AI-powered shopping assistant for Costco.com using Claude and the Model Context Protocol (MCP).

## Features

- **Search** - Find products on Costco.com with prices
- **Add to Cart** - Add items to your shopping cart
- **View Cart** - See current cart contents and totals
- **Checkout** - Navigate to checkout (with human-in-the-loop safety)

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/costco-cli.git
cd costco-cli

# Install dependencies
pip install -e .

# Install Playwright MCP Server
npx @anthropic-ai/mcp-server-playwright
```

## Prerequisites

- Python 3.10+
- Node.js (for npx/Playwright MCP)
- Anthropic API key set as `ANTHROPIC_API_KEY` environment variable

## Usage

```bash
# Show welcome screen
costco

# Search for products
costco search "kirkland coffee"

# Add item to cart
costco add "Kirkland Signature Colombian Coffee"

# View cart
costco cart

# Go to checkout (manual confirmation required)
costco checkout

# Set up persistent Chrome profile
costco setup
```

## Environment Variables

- `ANTHROPIC_API_KEY` - Your Anthropic API key (required)
- `COSTCO_CHROME_PROFILE` - Path to Chrome profile for persistent login

## Safety

This CLI will **never** complete a purchase automatically. The `checkout` command navigates to the final review page but requires you to manually click "Place Order" in the browser.

## Architecture

| Component | Technology |
|-----------|------------|
| CLI Host | Python (typer) |
| Orchestrator | Claude 3.7 Sonnet |
| Protocol | MCP (Model Context Protocol) |
| Automation | Playwright MCP Server |

## License

MIT
