# AEMET-MCP. Integration via MCP with the AEMET API

[![en](https://img.shields.io/badge/lang-en-red.svg)](README.md)
[![es](https://img.shields.io/badge/lang-es-yellow.svg)](README_es.md)

## DESCRIPTION

**AEMET is the State Meteorological Agency of Spain.**

**Aemet-mcp** allows you to retrieve historical climate data and meteorological information from the AEMET API directly from Claude AI and other MCP compatible clients, using the **Model Context Protocol (MCP)**.

Aemet-mcp is an MCP server that exposes tools enabling LLMs to query data from weather stations across Spain.

It includes secure handling of API keys and resource JSON files for using supporting data.

## KEY FEATURES

- Query for **historical daily values** (temperature, wind, precipitation, etc.)
- Access to **monthly climate summaries** by station.
- Filtering by year, month, and AEMET station code.
- Query beach conditions, including ultraviolet radiation indices.
- **Rainfall data analysis prompt** for Spanish municipalities with historical precipitation data
- Responses ready for use in JSON format.

## INSTALLATION

### Installing via Smithery

To install AEMET Weather Data Server for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@AnCode666/aemet-mcp):

```bash
npx -y @smithery/cli install @AnCode666/aemet-mcp --client claude
```

### Install with uv

### Prerequisites

- Python 3.10 or higher.
- [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager.

### Installing uv

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

### Install with Docker

You can also run AEMET-MCP using Docker:

#### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed on your system

#### Steps

1. **Build the Docker image:**

```bash
docker build -t aemet-mcp .
```

2. **Run the container:**

```bash
docker run -e AEMET_API_KEY=YOUR_AEMET_API_KEY aemet-mcp
```

Replace `YOUR_AEMET_API_KEY` with your actual API key from AEMET.

#### Integration with Claude Desktop using Docker

To use the Docker version with Claude Desktop, add this configuration to your `claude_desktop_config.json`:

```json
"aemet_mcp_docker": {
    "command": "docker",
    "args": [
        "run",
        "--rm",
        "-i",
        "-e", "AEMET_API_KEY=YOUR_AEMET_API_KEY",
        "aemet-mcp"
    ]
}
```

## INTEGRATION WITH CLIENTS LIKE CLAUDE DESKTOP

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

## USAGE EXAMPLES

Once properly configured, you can ask things like:

- "What's the weather like in Seville?"
- "Give me a list of the beaches in the province of Málaga"
- "Tell me the radiation levels at Maspalomas beach for tomorrow"
- "Give me the historical rainfall data for Albacete between January 1st, 2020 and February 1st, 2020"
- "Give me a list of the weather stations within a 50 km radius from the coordinates lat:40.4165, lon:-3.70256"

### Rainfall Data Analysis

The server includes a specialized prompt for analyzing historical precipitation data for Spanish municipalities. Use the `obtener_datos_lluvia_municipio` prompt with:

```
obtener_datos_lluvia_municipio("Madrid", "2023-01-01", "2023-12-31")
```

This prompt provides structured guidance for meteorological analysis, including:
- Municipality code search and validation
- Nearest weather station identification
- Historical precipitation data retrieval
- Statistical analysis and trend identification
- Climate pattern analysis with seasonal variations
- Data visualization recommendations

## DISTRIBUTIONS

### Smithery

[![smithery badge](https://smithery.ai/badge/@AnCode666/aemet-mcp)](https://smithery.ai/server/@AnCode666/aemet-mcp)

### Glama

<a href="https://glama.ai/mcp/servers/@AnCode666/aemet-mcp">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@AnCode666/aemet-mcp/badge" alt="AEMET-MCP MCP server" />
</a>

### MseeP

[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/ancode666-aemet-mcp-badge.png)](https://mseep.ai/app/ancode666-aemet-mcp)
[![Verified on MseeP](https://mseep.ai/badge.svg)](https://mseep.ai/app/ancode666-aemet-mcp)

### MCP Review

[MCP review certified](https://mcpreview.com/mcp-servers/ancode666/aemet-mcp)