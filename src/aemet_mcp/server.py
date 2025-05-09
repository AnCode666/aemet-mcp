from typing import Any
import httpx
import json
# from pathlib import Path
from importlib.resources import files
import logging
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import os

# Load data from .env file
load_dotenv()

# Init logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AemetMCPServer_eng")

# Init FastMCP server
mcp = FastMCP(
    "aemet-mcp",
    description="MCP server for querying the AEMET (Spanish State Meteorological Agency) API"
)

# Constants
AEMET_API_BASE = "https://opendata.aemet.es/opendata/api"
# Obtain API key from https://opendata.aemet.es/centrodedescargas/altaUsuario?
API_KEY = os.getenv("AEMET_API_KEY", "ND")

# Load beaches code from JSON file
json_path = files("aemet_mcp.res").joinpath("Beaches_code.json")
with open(json_path, encoding="utf-8") as f:
    CODIGOS_PLAYAS = json.load(f)

#with open(Path("./res/Beaches_code.json"), encoding="utf-8") as f:
#    CODIGOS_PLAYAS = json.load(f)


# Exact match dictionary
NOMBRE_A_CODIGO = {
    playa["NOMBRE_PLAYA"].lower(): playa["ID_PLAYA"] for playa in CODIGOS_PLAYAS
}
# Dictionary of provinces → list of beaches
PROVINCIA_A_PLAYAS = {}
for playa in CODIGOS_PLAYAS:
    provincia = playa["NOMBRE_PROVINCIA"].lower()
    PROVINCIA_A_PLAYAS.setdefault(provincia, []).append(playa)


async def make_aemet_request(url: str) -> dict[str, Any] | None:
    """Make a request to the AEMET API with proper error handling."""

    logger.info(f"make_aemet_request")

    headers = {
        "api_key": API_KEY,
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # The AEMET API first returns a data URL
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            data_info = response.json()
            
            # Fetch the real data from the URL returned by the API
            if data_info.get("estado") == 200:
                data_url = data_info.get("datos")
                if data_url:
                    data_response = await client.get(data_url, timeout=30.0)
                    data_response.raise_for_status()
                    # Handle encoding properly
                    content = data_response.content.decode('latin1')
                    return json.loads(content)
            return None
        except Exception as e:
            logger.error(f"Error connecting to AEMET: {str(e)}")
            return None

def buscar_playas_por_nombre(nombre_parcial: str):
    nombre_parcial = nombre_parcial.lower()
    return [
        playa for playa in CODIGOS_PLAYAS
        if nombre_parcial in playa["NOMBRE_PLAYA"].lower()
        or playa["NOMBRE_PROVINCIA"].lower() in nombre_parcial
    ]


@mcp.tool()
async def get_daily_forecast(municipality_code: str) -> str:
    """Get the daily weather forecast for a Spanish municipality.
    
    Args:
        municipality_code: AEMET municipality code (e.g., "28079" for Madrid)
    """
    url = f"{AEMET_API_BASE}/prediccion/especifica/municipio/diaria/{municipality_code}"
    data = await make_aemet_request(url)
    
    if not data:
        return "No forecast data could be obtained for this municipality.."
    
    try:
        forecast = data[0]
        prediction = forecast.get("prediccion", {})
        day = prediction.get("dia", [])[0]
        
        result = f"""
Municipality: {forecast.get('nombre', 'Desconocido')}
Date: {day.get('fecha', 'Desconocida')}

Temperature:
  Maximum: {day.get('temperatura', {}).get('maxima', 'N/D')}°C
  Minimum: {day.get('temperatura', {}).get('minima', 'N/D')}°C

State of the Sky: {day.get('estadoCielo', [{}])[0].get('descripcion', 'N/D')}
Probability of Rain: {day.get('probPrecipitacion', [{}])[0].get('value', 'N/D')}%
Wind: {day.get('viento', [{}])[0].get('velocidad', 'N/D')} km/h {day.get('viento', [{}])[0].get('direccion', '')}
"""
        return result
    except Exception as e:
        return f"Error processing forecast data: {str(e)}"

@mcp.tool()
async def get_station_data(station_id: str) -> str:
    """Obtain specific weather data for a weather station.
    
    Args:
        station_id: Station identifier (e.g., "8416Y" for Valencia))
    """
    url = f"{AEMET_API_BASE}/observacion/convencional/datos/estacion/{station_id}"
    data = await make_aemet_request(url)
    
    if not data:
        return "No meteorological data could be obtained for this station.."
    
    try:
        latest = data[0]
        result = f"""
station: {latest.get('ubi', 'Desconocida')}
Hour: {latest.get('fint', 'Desconocida')}

Temperature: {latest.get('ta', 'N/D')}°C
Humidity: {latest.get('hr', 'N/D')}%
Wind Speed: {latest.get('vv', 'N/D')} m/s
Wind Direction: {latest.get('dv', 'N/D')}°
Pressure: {latest.get('pres', 'N/D')} hPa
Precipitation (1h): {latest.get('prec', 'N/D')} mm
"""
        return result
    except Exception as e:
        return f"Error when processing weather data: {str(e)}"

@mcp.tool()
async def get_station_list() -> str:
    """Get a list of all available weather stations."""
    url = f"{AEMET_API_BASE}/valores/climatologicos/inventarioestaciones/todasestaciones"
    data = await make_aemet_request(url)
    
    if not data:
        return "Could not obtain the list of stations."
    
    try:
        stations = []
        for station in data:
            stations.append(f"ID: {station.get('indicativo', 'N/D')} - {station.get('nombre', 'Desconocido')} ({station.get('provincia', 'Desconocida')})")
        
        return "\n".join(stations)
    except Exception as e:
        return f"Error while processing station data: {str(e)}"

@mcp.tool()
async def get_historical_data(station_id: str, start_date: str, end_date: str) -> str:
    """Obtain historical meteorological data for a specific station.
    
    Args:
        station_id: Identifier of the station (e.g. "3195" for Madrid Retiro)
        start_date: Start date in format YYYYY-MM-DD
        end_date: End date in format YYYYY-MM-DD
    """
    # Format dates for the AEMET API (AAAA-MM-DDTHH:MM:SSUTC)
    start = start_date + "T00:00:00UTC"
    end = end_date + "T23:59:59UTC"
    
    url = f"{AEMET_API_BASE}/valores/climatologicos/diarios/datos/fechaini/{start}/fechafin/{end}/estacion/{station_id}"
    data = await make_aemet_request(url)
    
    if not data:
        return "No historical data could be obtained for this station."
    
    try:
        result = []
        result.append(f"Historical data for the station {station_id}")
        result.append(f"Period: {start_date} a {end_date}\n")
        
        for day in data:
            date = day.get('fecha', 'Fecha Desconocida')
            result.append(f"Date: {date}")
            result.append(f"Maximum Temperature: {day.get('tmax', 'N/D')}°C")
            result.append(f"Minimum Temperature: {day.get('tmin', 'N/D')}°C")
            result.append(f"Average Temperature: {day.get('tmed', 'N/D')}°C")
            result.append(f"Precipitation: {day.get('prec', 'N/D')} mm")
            result.append(f"Wind Speed: {day.get('velmedia', 'N/D')} km/h")
            result.append(f"Maximum Wind Speed: {day.get('racha', 'N/D')} km/h")
            result.append(f"Sun Hours: {day.get('sol', 'N/D')} hours")
            result.append("-" * 40 + "\n")
        
        return "\n".join(result)
    except Exception as e:
        return f"Error when processing historical data: {str(e)}"

@mcp.tool()
async def monthly_climate_data(station_id: str, year: int, month: int) -> str:
    """Retrieve monthly climatological data for a specific weather station.
    
    Args:
        station_id: Weather station identifier (e.g., "3195" for Madrid Retiro).
        year: Year (YYYY).
        month: Month (1-12).
        
    Returns:
        A formatted string with the monthly climate summary, or an error message if no data is available.
    """
    month_str = str(month).zfill(2)
    url = f"{AEMET_API_BASE}/valores/climatologicos/mensualesanuales/datos/anioini/{year}/aniofin/{year}/estacion/{station_id}"
    data = await make_aemet_request(url)

    if not data:
        return "Unable to retrieve monthly climate data for this station."

    try:
        result = []
        record = next((r for r in data if r.get("fecha", "").split("-")[-1] == month_str), None)
        
        if not record:
            return f"No data available for station {station_id} for {year}-{month_str}."

        result.append(f"Monthly Climate Summary for Station {record.get('nombre', station_id)} ({station_id})")
        result.append(f"Province: {record.get('provincia', 'N/A')}")
        result.append(f"Altitude: {record.get('altitud', 'N/A')} m")
        result.append(f"Year: {year}, Month: {month}\n")

        # Temperature
        result.append(f"Avg Max Temperature: {record.get('tm_max', 'N/A')} °C")
        result.append(f"Avg Min Temperature: {record.get('tm_min', 'N/A')} °C")
        result.append(f"Avg Temperature: {record.get('tm_mes', 'N/A')} °C")
        result.append(f"Abs Max Temperature: {record.get('ta_max', 'N/A')} °C")
        result.append(f"Abs Min Temperature: {record.get('ta_min', 'N/A')} °C")

        # Precipitation
        result.append(f"Total Precipitation: {record.get('p_mes', 'N/A')} mm")
        result.append(f"Max Daily Precipitation: {record.get('p_max', 'N/A')}")
        result.append(f"Rainy Days: {record.get('n_llu', 'N/A')}")
        result.append(f"Snowy Days: {record.get('n_nie', 'N/A')}")
        result.append(f"Stormy Days: {record.get('n_tor', 'N/A')}")
        result.append(f"Foggy Days: {record.get('n_fog', 'N/A')}")

        # Humidity and Solar
        result.append(f"Avg Relative Humidity: {record.get('hr', 'N/A')}%")
        result.append(f"Avg Daily Sunshine: {record.get('inso', 'N/A')} h")
        result.append(f"Sunshine Percent (vs theoretical): {record.get('p_sol', 'N/A')}%")

        # Wind
        result.append(f"Max Wind Gust: {record.get('w_racha', 'N/A')}")
        result.append(f"Avg Wind Speed: {record.get('w_med', 'N/A')} km/h")
        result.append(f"Days with Wind >= 55 km/h: {record.get('nw_55', 'N/A')}")
        result.append(f"Days with Wind >= 91 km/h: {record.get('nw_91', 'N/A')}")

        # Pressure
        result.append(f"Avg Station Pressure: {record.get('q_med', 'N/A')} hPa")
        result.append(f"Max Pressure: {record.get('q_max', 'N/A')} hPa")
        result.append(f"Min Pressure: {record.get('q_min', 'N/A')} hPa")
        result.append(f"Avg Sea-level Pressure: {record.get('q_mar', 'N/A')} hPa")

        return "\n".join(result)

    except Exception as e:
        return f"Error processing monthly climate data: {str(e)}"

@mcp.tool()
def solve_beach_code(nombre_o_codigo: str) -> str:
    """
    Resolve the exact name and code of a beach from a partial name or code.

    Args:
        beach_name_or_code: Beach name or code.

    Returns:
        Correct beach name and its BEACH_ID, or a list of matches/suggestions.
    """
    entrada = nombre_o_codigo.strip().lower()

    # If it's a number, check whether it corresponds to an ID_PLAYA
    if entrada.isdigit():
        for playa in CODIGOS_PLAYAS:
            if str(playa["ID_PLAYA"]) == entrada:
                return (
                    f"Exact match:\n"
                    f"Name: {playa['NOMBRE_PLAYA']}\n"
                    f"Code: {playa['ID_PLAYA']}\n"
                    f"Province Code: {playa['NOMBRE_PROVINCIA']}\n"
                    f"Municipality: {playa['NOMBRE_MUNICIPIO']}"
                )
        return f"No beaches were found with the code {nombre_o_codigo}."

    # Search for partial name matches
    coincidencias = buscar_playas_por_nombre(entrada)

    if len(coincidencias) == 0:
        return f"No beaches were found that match with '{nombre_o_codigo}'."

    if len(coincidencias) == 1:
        playa = coincidencias[0]
        return (
            f"Exact match:\n"
            f"Name: {playa['NOMBRE_PLAYA']}\n"
            f"Code: {playa['ID_PLAYA']}\n"
            f"Province: {playa['NOMBRE_PROVINCIA']}\n"
            f"Municipality: {playa['NOMBRE_MUNICIPIO']}"
        )

    # In case of several matches
    listado = "\n".join(
        f"- {p['NOMBRE_PLAYA']} (Código: {p['ID_PLAYA']}, {p['NOMBRE_PROVINCIA']})"
        for p in coincidencias
    )
    return (
        f"Several matches were found for '{nombre_o_codigo}':\n"
        f"{listado}\nPlease, specify full name or exact code."
    )

@mcp.tool()
async def get_beach_data_uv(nombre_o_codigo: str, dias_frc: int, tipo_consulta: str = "playa") -> str:
    """Query information on beaches or UV index from AEMET.

    Args:
        name_or_code: Partial or full name of the beach, or its BEACH_ID. Also accepts 'list' or 'list:<province>'.
        dias_frc: Number of forecast days, starting form 0, which means 0 days from today, to 4, which means 4 days from today.
        query_type: 'beach' for forecast, 'UV_index' for UV index, must be in english.

    Returns:
        Requested information or list of matches.
    """
    comando = nombre_o_codigo.strip().lower()

    if comando == "list":
        return "Available beaches:\n" + "\n".join(
            f"{p['NOMBRE_PLAYA']} ({p['NOMBRE_PROVINCIA']})"
            for p in sorted(CODIGOS_PLAYAS, key=lambda x: x["NOMBRE_PLAYA"])
        )

    if comando.startswith("list:"):
        provincia = comando.split("list:", 1)[1].strip()
        playas = PROVINCIA_A_PLAYAS.get(provincia.lower())
        if not playas:
            return f"No beaches found for the province '{provincia}'."
        return f"Beaches in {provincia.title()}:\n" + "\n".join(
            p["NOMBRE_PLAYA"] for p in sorted(playas, key=lambda x: x["NOMBRE_PLAYA"])
        )

    # Check if it is a direct code (ID_PLAYA)
    if nombre_o_codigo.isdigit():
        codigo = nombre_o_codigo
        nombre_mostrado = codigo
    else:
        nombre_normalizado = nombre_o_codigo.lower()
        if nombre_normalizado in NOMBRE_A_CODIGO:
            codigo = str(NOMBRE_A_CODIGO[nombre_normalizado])
            nombre_mostrado = nombre_o_codigo
        else:
            coincidencias = buscar_playas_por_nombre(nombre_normalizado)
            if len(coincidencias) == 0:
                return f"No matches found for '{nombre_o_codigo}'. Use “list” to view all options."
            elif len(coincidencias) == 1:
                codigo = str(coincidencias[0]["ID_PLAYA"])
                nombre_mostrado = coincidencias[0]["NOMBRE_PLAYA"]
            else:
                opciones = "\n".join(
                    f"{p['NOMBRE_PLAYA']} ({p['NOMBRE_PROVINCIA']}, {p['NOMBRE_MUNICIPIO']})"
                    for p in coincidencias
                )
                return f"Several matches were found for '{nombre_o_codigo}':\n{opciones}\nPlease, specify full name."

    # Construct URL
    if tipo_consulta == "beach":
        url = f"{AEMET_API_BASE}/prediccion/especifica/playa/{codigo}"
    elif tipo_consulta == "UV_index":
        url = f"{AEMET_API_BASE}/prediccion/especifica/uvi/{dias_frc}"
    else:
        return "Invalid query type. Use 'beach' or 'UV_index'."

    datos = await make_aemet_request(url)

    if not datos:
        return f"No data could be obtained from {tipo_consulta} for the code {codigo}."

    try:
        return f"Data from {tipo_consulta} for '{nombre_mostrado}':\n{json.dumps(datos, indent=2, ensure_ascii=False)}"
    except Exception as e:
        return f"Error processing data from {tipo_consulta}: {str(e)}"


# Main function
def main():
    """Arrancar el servidor mcp"""
    mcp.run()

if __name__ == "__main__":
    mcp.run(transport='stdio')