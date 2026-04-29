import requests
from datetime import date
from secrets_util import secret_or_env


from libraries.logger import get_logger
logger = get_logger(__name__)

class Growatt:
    def __init__(self):
        self.url = secret_or_env("GROWATT_URL")
        self.token = secret_or_env("GROWATT_TOKEN")
        self.sn = secret_or_env("GROWATT_SN")
        self.type = secret_or_env("GROWATT_TYPE")


    def get_production(self) -> tuple[str, str, str]:
        logger.info("Fetching Growatt %s", self.url)
        response = requests.post(
            self.url,
            headers = {
                "token": self.token,
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={
                "deviceSn": self.sn,
                "deviceType": self.type,
                "date": date.today().strftime("%Y-%m-%d")
            }
        )

        eac_today = response.json()["data"]["datas"][0]["eacToday"]

        return eac_today, "", ""