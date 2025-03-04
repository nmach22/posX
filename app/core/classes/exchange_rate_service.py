import requests


EXCHANGE_RATE_API_KEY = "616d00e9b7800f1a1aade2d3"


class ExchangeRateService:
    def get_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_RATE_API_KEY}/latest/{from_currency}"
        response = requests.get(url)
        data = response.json()

        if data.get("result") == "success":
            conversion_rate = data["conversion_rates"].get(to_currency)
            if conversion_rate:
                return conversion_rate
            else:
                raise ValueError(f"Conversion rate for {to_currency} not found.")
        else:
            raise ValueError(
                f"Error fetching exchange rate data: {data.get('error-type')}"
            )
