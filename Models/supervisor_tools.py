from langchain_core.tools import tool

@tool
def get_user_location() -> str:
    """
    Use this tool to get the user's current GPS location.
    """
    print("--- TOOL CALLED: get_user_location ---")
    return "Nashik, Maharashtra, India"

@tool
def fetch_contextual_data(location: str) -> str:
    """
    Use this tool to fetch agricultural and market data for a specific location.
    Simulates calling government APIs for weather, soil, and market prices.
    """
    print(f"--- TOOL CALLED: fetch_contextual_data for {location} ---")
    agricultural_data = "Soil Type: Black Cotton Soil, Avg Temp: 28°C, Rainfall Forecast: Light showers."
    market_data = "Current Mandi Prices (Nashik): Grapes - ₹80/kg, Onions - ₹25/kg."
    return f"Agricultural Context: {agricultural_data}\nMarket Context: {market_data}"
