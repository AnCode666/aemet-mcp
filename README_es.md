# AEMET-MCP. Integración vía MCP con la API de AEMET

[![en](https://img.shields.io/badge/lang-en-red.svg)](README.md)
[![es](https://img.shields.io/badge/lang-es-yellow.svg)](README_es.md)

## DESCRIPCIÓN

**AEMET es la Agencia Estatal de Meteorología de España.**

**Aemet-mcp** permite obtener datos climatológicos históricos y datos meteorológicos de la API de AEMET directamente desde Claude AI y otros clientes MCP compatibles, utilizando el protocolo **Model Context Protocol (MCP)**.

Aemet-mcp Es un servidor MCP que expone herramientas para que los LLM puedan consultar los datos de las estaciones meteorológicas de España.

Incluye el manejo seguro de claves de API y recursos en formato json para el empleo de datos de apoyo.

## CARACTERÍSTICAS PRINCIPALES

- Consulta de **valores diarios históricos** (temperatura, viento, precipitaciones, etc.)
- Acceso a **resúmenes climatológicos mensuales** por estación.
- Filtrado por año, mes y código de estación AEMET.
- Consulta del estado de las playas, incluyendo índices de radiación ultravioleta.
- Respuestas listas para utilizar en formato JSON.

## INSTALACIÓN

### Instalar desde Smithery

Puedes instalar aemet-mcp en Claude para Escritorio automáticamente mediante [Smithery](https://smithery.ai/server/@AnCode666/aemet-mcp):

```bash
npx -y @smithery/cli install @AnCode666/aemet-mcp --client claude
```

### Instalar con uv

### Prerrequisitos

- Python 3.10 o superior.
- [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager.

### Instalación de uv

Lo primero que hay que hacer es instalar `uv`, que es un gestor de paquetes para Python.
**Se instala desde la consola**.

En MAC y Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

En Windows:

```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

También se puede instalar con pip:

```bash
pip install uv
```

Para más información sobre la instalación de **uv**, consulta la [documentación oficial](https://docs.astral.sh/uv/getting-started/installation/).

## INTEGRACIÓN CON CLIENTES COMO CLAUDE PARA ESCRITORIO

Una vez que tenemos **uv** instalado, ya podemos usar el servidor MCP desde cualquier cliente compatible, como Claude para Escritorio, en cuyo caso los pasos a seguir son los siguientes:

1. Ve a **Claude > Settings > Developer > Edit Config > `claude_desktop_config.json`**.
2. Agrega el siguiente bloque de código dentro de `"mcpServers"`:

```json
"aemet_mcp_": {
    "command": "uvx",
    "args": [
        "aemet_mcp"
    ],
    "env": {
        "AEMET_API_KEY": "TU_API_KEY_DE_AEMET"
    }
}
```

3. Obtener una clave de API gratuita de AEMET en: <https://opendata.aemet.es/centrodedescargas/altaUsuario>
4. Sustituir donde pone YOUR_AEMET_API_KEY por la clave de API obtenida (dejar las comillas puestas):
5. Si ya tienes otro servidor MCP configurado en tu cliente, separa cada servidor con una coma `,`.

En general, para integrarlo en cualquier otro cliente compatible con MCP, como pueden ser Cursor, CODEGPT o Roo Code, solamente hay que ir a la correspondiente configuración de los servidores MCP del cliente y añadir el mismo bloque de código.

## EJEMPLOS DE USO

Una vez configurado correctamente, podrás pedirle cosas como:

- ¿Qué tiempo hace en Sevilla?
- Dame un listado de as playas que hay en la provincia de Málaga
- Dime los niveles de radiación en la playa de Maspalomas para mañana
- Dime los datos históricos de lluvia en Albacete entre el 1 de enero de 2020 y el 1 de febrero de 2020
- Dame un listado de las estaciones meteorológicas en un radio de 50 km respecto a las coordenadas lat:40.4165, lon:-3.70256.

## DISTRIBUCIONES

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

[Certificado en MCP review](https://mcpreview.com/mcp-servers/ancode666/aemet-mcp)