import httpx


url = "https://api.nobitex.ir/market/stats"

response = httpx.get(url=url)

data = response.json()


# currency => from user
# price => from api
latest_price = data["stats"]["btc-rls"]["latest"]

print(data["stats"]["btc-rls"]["latest"])