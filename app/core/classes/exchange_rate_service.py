import os

import requests
from dotenv import load_dotenv

load_dotenv()


class ExchangeRateService:
    key = os.environ.get("EXCHANGE_RATE_API_KEY")

    def get_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        url = f"https://v6.exchangerate-api.com/v6/{self.key}/latest/{from_currency}"
        response = requests.get(url)
        data = response.json()

        if data.get("result") == "success":
            conversion_rate = data["conversion_rates"].get(to_currency)
            if conversion_rate:
                return float(conversion_rate)
            else:
                raise ValueError(f"Conversion rate for {to_currency} not found.")
        else:
            raise ValueError(
                f"Error fetching exchange rate data: {data.get('error-type')}"
            )
