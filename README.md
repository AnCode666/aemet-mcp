[![en](https://img.shields.io/badge/lang-en-red.svg)](README.md)
[![es](https://img.shields.io/badge/lang-es-yellow.svg)](README_es.md)

# AEMET-MCP. Integration via MCP with the AEMET API

**AEMET is the State Meteorological Agency of Spain.**

**Aemet-mcp** allows you to retrieve historical climate data and meteorological information from the AEMET API directly from Claude AI and other MCP compatible clients, using the **Model Context Protocol (MCP)**.

Aemet-mcp is an MCP server that exposes tools enabling LLMs to query data from weather stations across Spain.

It includes secure handling of API keys and resource JSON files for using supporting data.

## Key Features

- Query for **historical daily values** (temperature, wind, precipitation, etc.)
- Access to **monthly climate summaries** by station.
- Filtering by year, month, and AEMET station code.
- Query beach conditions, including ultraviolet radiation indices.
- Responses ready for use in JSON format.

## Installation

### Prerequisites

- Python 3.10 or higher.
- [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager.

## Installing uv

The first step is to install `uv`, a package manager for Python.  
**It can be installed from the command line**.

On macOS and Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

On Windows:  

```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

You can also install it with pip:  

```bash
pip install uv
```

For more information about installing uv, visit the [uv documentation](https://docs.astral.sh/uv/getting-started/installation/).

## Integration with clients like Claude for Desktop

Once **uv** is installed, you can use the MCP server from any compatible client such as Claude for Desktop, in which case the steps to follow are:

1. Go to **Claude > Settings > Developer > Edit Config > `claude_desktop_config.json`**
2. Add the following block inside `"mcpServers"`:

```json
"aemet_mcp_": {
    "command": "uvx",
    "args": [
        "aemet_mcp"
    ],
    "env": {
        "AEMET_API_KEY": "YOUR_AEMET_API_KEY"
    }
}
```

3. Get a free API key from AEMET at: <https://opendata.aemet.es/centrodedescargas/altaUsuario>
4. Replace `YOUR_AEMET_API_KEY` with your actual API key (leave the quotes).
5. If you already have another MCP server configured, separate each with a comma `,`.

In general, to integrate it into any other MCP-compatible client such as Cursor, CODEGPT, or Roo Code, simply go to the MCP server configuration of your client and add the same code block.

## Usage Examples

Once properly configured, you can ask things like:

```
- "What's the weather like in Seville?"
- "Tell me the radiation levels at Maspalomas beach for tomorrow"
- "Give me the historical rainfall data for Albacete between January 1st, 2020 and February 1st, 2020"
```
