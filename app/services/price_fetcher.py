from fastapi import HTTPException
import httpx




async def fetch_latest_price(currency: str) -> float:
    url = "https://api.nobitex.ir/market/stats"
    
    response = httpx.get(url=url)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch market data")

    data = response.json()

    available_currencies = data["stats"].keys()  

    currency_key = f"{currency.lower()}-usdt"

    if currency_key not in available_currencies:
        raise HTTPException(
            status_code=404, 
            detail=f"Currency not found. Available currencies are: {', '.join(available_currencies)}"
        )

    return float(data["stats"][currency_key]["latest"])