from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import httpx
from typing import Any, Literal
import unicodedata
import json
from importlib.resources import files
import logging
import os
import difflib
from math import radians, cos, sin, asin, sqrt

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AemetMCPServer")

mcp = FastMCP(
    "aemet-mcp",
    description="MCP server for querying the AEMET (Spanish State Meteorological Agency) API"
)

AEMET_API_BASE = "https://opendata.aemet.es/opendata/api"
API_KEY = os.getenv("AEMET_API_KEY", "ND")

CODIGOS_PLAYAS = json.loads(
    files("aemet_mcp.res")
    .joinpath("Beaches_code.json")
    .read_text(encoding="utf-8")
)

NOMBRE_A_CODIGO = {
    playa["NOMBRE_PLAYA"].lower(): playa["ID_PLAYA"] for playa in CODIGOS_PLAYAS
}
PROVINCIA_A_PLAYAS = {}
for playa in CODIGOS_PLAYAS:
    provincia = playa["NOMBRE_PROVINCIA"].lower()
    PROVINCIA_A_PLAYAS.setdefault(provincia, []).append(playa)

MUNICIPIOS = json.loads(
    files("aemet_mcp.res")
    .joinpath("Municipallity_code.json")
    .read_text(encoding="utf-8")
)

PROVINCIAS = json.loads(
    files("aemet_mcp.res")
    .joinpath("Provinces_code.json")
    .read_text(encoding="utf-8")
)

# Invertimos el dict para obtener código → nombre
CODIGO_A_PROVINCIA = {code.zfill(2): name for code, name in PROVINCIAS.items()}


async def make_aemet_request(url: str) -> dict[str, Any] | list[Any] | None:
    logger.info(f"make_aemet_request")
    headers = {
        "api_key": API_KEY,
        "Accept": "application/json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            data_info = response.json()
            if data_info.get("estado") == 200:
                data_url = data_info.get("datos")
                if data_url:
                    data_response = await client.get(data_url, timeout=30.0)
                    data_response.raise_for_status()
                    content = data_response.content.decode('latin1')
                    return json.loads(content)
            return None
        except Exception as e:
            logger.error(f"Error connecting to AEMET: {str(e)}")
            return None
        
def normalize(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()

def haversine(lat1, lon1, lat2, lon2):
    # Distancia entre dos coordenadas en km
    R = 6371.0  # radio de la Tierra en km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c

def sexagesimal_to_decimal(coord: str) -> float:
    """
    Convert AEMET-style sexagesimal string to decimal degrees.
    Examples:
        '424607N' -> 42.768611
        '070103W' -> -7.0175
    """

    direction = coord[-1]
    coord = coord[:-1]

    degrees = int(coord[:2])
    minutes = int(coord[2:4])
    seconds = int(coord[4:])

    decimal = degrees + minutes / 60 + seconds / 3600
    if direction in 'SW':
        decimal = -decimal

    return decimal


@mcp.tool()
    
async def search_municipality_code(nombre: str):
    """
    Search Spanish municipalities by name or province (accent-insensitive, typo-tolerant).

    Args:
        nombre: Partial or approximate name of a municipality or province.

    Returns:
        A list of matching municipalities with their codes and provinces.
    """
    entrada = normalize(nombre.strip())
    resultados = []

    for municipio, codigo in MUNICIPIOS.items():
        nombre_mun = normalize(municipio)
        cod_prov = codigo[:2]
        nombre_prov = normalize(CODIGO_A_PROVINCIA.get(cod_prov, ""))

        # Coincidencia exacta o parcial
        if entrada in nombre_mun or entrada in nombre_prov:
            resultados.append({
                "municipio": municipio,
                "codigo": codigo,
                "provincia": CODIGO_A_PROVINCIA.get(cod_prov, "")
            })
        # Coincidencia aproximada
        elif any(difflib.SequenceMatcher(None, entrada, campo).ratio() > 0.75 for campo in [nombre_mun, nombre_prov]):
            resultados.append({
                "municipio": municipio,
                "codigo": codigo,
                "provincia": CODIGO_A_PROVINCIA.get(cod_prov, "")
            })

    if not resultados:
        return {"error": f"No municipality matches found for '{nombre}'."}

    return resultados

@mcp.tool()
async def get_daily_forecast(municipality_code: str):
    """Get the daily weather forecast for a Spanish municipality.
    
    Args:
        municipality_code: AEMET municipality code (e.g., "28079" for Madrid)
    """

    url = f"{AEMET_API_BASE}/prediccion/especifica/municipio/diaria/{municipality_code}"
    return await make_aemet_request(url)

@mcp.tool()
async def get_station_data(station_id: str):
    """Obtain specific weather data for a weather station.
    
    Args:
        station_id: Station identifier (e.g., "8416Y" for Valencia))
    """

    url = f"{AEMET_API_BASE}/observacion/convencional/datos/estacion/{station_id}"
    return await make_aemet_request(url)

@mcp.tool()
async def get_station_list(search_terms: str = ""):
    """
    Get a list of all available weather stations or filter by one or more search terms, including approximate matches.

    Args:
        search_terms: Optional terms (space or comma separated) to filter stations by name or province.
    """
    url = f"{AEMET_API_BASE}/valores/climatologicos/inventarioestaciones/todasestaciones"
    stations = await make_aemet_request(url)

    if not stations:
        return None

    if not search_terms:
        logger.info("No search terms provided")
        return stations

    terms = search_terms.replace(',', ' ').split()
    search_terms_normalized = [normalize(term) for term in terms]
    filtered = []
    numCoincidencias = 0

    for station in stations:
        if not isinstance(station, dict):
            continue

        nombre = normalize(station.get("nombre", ""))
        provincia = normalize(station.get("provincia", ""))

        for term in search_terms_normalized:
            if term in nombre or term in provincia:
                filtered.append(station)
                numCoincidencias += 1
                break

    logger.info(f"Filtered stations: {numCoincidencias}")
    return filtered

@mcp.tool()
async def find_nearby_stations(lat: float, lon: float, radio_km: float = 25):
    """
    Find weather stations within a given radius (in km) from a given geographic coordinate.

    Args:
        lat: Latitude in decimal degrees (e.g., 43.36)
        lon: Longitude in decimal degrees (e.g., -8.41)
        radio_km: Search radius in kilometers
    """

    url = f"{AEMET_API_BASE}/valores/climatologicos/inventarioestaciones/todasestaciones"
    estaciones = await make_aemet_request(url)
    if not estaciones:
        return {"error": "Could not retrieve station list."}

    resultado = []
    for est in estaciones:
        try:
            est_dict: dict = est  # type: ignore
            est_lat = sexagesimal_to_decimal(est_dict["latitud"])
            est_lon = sexagesimal_to_decimal(est_dict["longitud"])
            dist = haversine(lat, lon, est_lat, est_lon)
            if dist <= radio_km:
                est_dict["distancia_km"] = round(dist, 2)
                resultado.append(est_dict)
        except Exception:
            continue

    return resultado
    #return sorted(resultado, key=lambda x: x["distancia_km"])

@mcp.tool()
async def get_historical_data(station_id: str, start_date: str, end_date: str):
    """Obtain historical meteorological data for a specific station.
    
    Args:
        station_id: Identifier of the station (e.g. "3195" for Madrid Retiro)
        start_date: Start date in format YYYYY-MM-DD
        end_date: End date in format YYYYY-MM-DD
    """

    start = start_date + "T00:00:00UTC"
    end = end_date + "T23:59:59UTC"
    url = f"{AEMET_API_BASE}/valores/climatologicos/diarios/datos/fechaini/{start}/fechafin/{end}/estacion/{station_id}"
    return await make_aemet_request(url)

@mcp.tool()
async def monthly_climate_data(station_id: str, year: int, month: int):
    """Retrieve monthly climatological data for a specific weather station.
    
    Args:
        station_id: Weather station identifier (e.g., "3195" for Madrid Retiro).
        year: Year (YYYY).
        month: Month (1-12).
        
    Returns:
        A JSON with the monthly climate summary.
    """

    url = f"{AEMET_API_BASE}/valores/climatologicos/mensualesanuales/datos/anioini/{year}/aniofin/{year}/estacion/{station_id}"
    return await make_aemet_request(url)

@mcp.tool()
def solve_beach_code(nombre: str, tipo: Literal["playa", "provincia", "municipio"] = "playa"):
    """
    Search beaches by name, province, or municipality.

    Args:
        nombre: Search string (accent-insensitive)
        tipo: One of 'playa', 'provincia', or 'municipio'
    """
    entrada = normalize(nombre.strip())
    coincidencias = []

    for playa in CODIGOS_PLAYAS:
        if tipo == "playa":
            campo = normalize(playa.get("NOMBRE_PLAYA", ""))
        elif tipo == "provincia":
            campo = normalize(playa.get("NOMBRE_PROVINCIA", ""))
        elif tipo == "municipio":
            campo = normalize(playa.get("NOMBRE_MUNICIPIO", ""))
        else:
            return {"error": f"Invalid type '{tipo}'. Use 'playa', 'provincia' or 'municipio'."}

        if entrada in campo or difflib.SequenceMatcher(None, entrada, campo).ratio() > 0.75:
            coincidencias.append(playa)

    if not coincidencias:
        return {"error": f"No beaches found with {tipo} matching '{nombre}'."}
    return coincidencias

@mcp.tool()
async def get_beach_data_uv(nombre_o_codigo: str, dias_frc: int, tipo_consulta: str = "playa"):
    """Query information on beaches or UV index from AEMET.

    Args:
        name_or_code: Partial or full name of the beach, or its BEACH_ID. Also accepts 'list' or 'list:<province>'.
        dias_frc: Number of forecast days, starting form 0, which means 0 days from today, to 4, which means 4 days from today.
        query_type: 'beach' for forecast, 'UV_index' for UV index, must be in english.

    Returns:
        Requested information or list of matches.
    """
    comando = normalize(nombre_o_codigo.strip())

    if comando == "list":
        return sorted(CODIGOS_PLAYAS, key=lambda x: normalize(x["NOMBRE_PLAYA"]))

    if comando.startswith("list:"):
        provincia = normalize(comando.split("list:", 1)[1].strip())
        return PROVINCIA_A_PLAYAS.get(provincia, [])

    if nombre_o_codigo.isdigit():
        codigo = nombre_o_codigo
    else:
        coincidencias = [
            p for p in CODIGOS_PLAYAS
            if comando in normalize(p["NOMBRE_PLAYA"]) or comando in normalize(p["NOMBRE_PROVINCIA"])
        ]
        if len(coincidencias) == 1:
            codigo = str(coincidencias[0]["ID_PLAYA"])
        elif coincidencias:
            return coincidencias
        else:
            return {"error": f"No matches found for '{nombre_o_codigo}'."}

    url = f"{AEMET_API_BASE}/prediccion/especifica/{'playa' if tipo_consulta == 'beach' else 'uvi'}/{codigo if tipo_consulta == 'beach' else dias_frc}"
    return await make_aemet_request(url)

# Main function
def main():
    """Arrancar el servidor mcp"""
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()