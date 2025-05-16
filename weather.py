from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("weather")

MWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

async def make_nws_request(url: str) -> dict[str, Any] | None:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json",
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")
            return None
        
def format_alert(feature: dict) -> str:
    props = feature["properties"]
    return f"""
Event: {props['event', 'Unknown']}
Area: {props['areaDesc', 'Unknown']}
Severity: {props['severity', 'Unknown']}
Description: {props['description', 'No desc available']}
Instruction: {props['instruction', 'No instruction available']}
"""

@mcp.tool()
async def get_alerts(state: str) -> str:
    """ Get weather alerts"""
    url = f"{MWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)
    
    if not data or "features" not in data:
        return "Unable to fetch or no alerts found"
    
    if not data["features"]:
        return "No active alerts found"
    
    alerts = []
    for feature in data["features"]:
        alerts.append(format_alert(feature))
    
    return "\n".join(alerts)

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """ Get weather forecast for a specific location"""
    url = f"{MWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(url)
    
    if not points_data:
        return "Unable to fetch forecast data for this location"
    
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)
    
    if not forecast_data:
        return "Unable to fetch forecast data"
    
    forecasts = []
    for period in forecast_data["properties"]["periods"]:
        forecast = f"""
        {period['name']}:
        Temperature: {period['temperature']}"{period['temperatureUnit']}
        Wind: {period['windSpeed']} {period['windDirection']}
        Forecast: {period['detailedForecast']}
        """
        forecasts.append(forecast)
    
    return "\n---\n".join(forecasts)

# Run the MCP server
if __name__ == "__main__":
    mcp.run(transport="stdio")
