import base64
import datetime
import time
import jwt
import requests

from errors import UserError


class StatisticsAPI:
    def __init__(self, api_url, template_id, basic_username, basic_password, app_username, app_password):
        self.api_url = api_url
        self.template_id = template_id
        self.basic_username = basic_username
        self.basic_password = basic_password
        self.app_username = app_username
        self.app_password = app_password
        self._jwt_token = None

    def send_data(self, price: float, name: str) -> None:
        auth_token = self._ensure_auth()
        response = requests.post(
            url=f"{self.api_url}/api/data/{self.template_id}/day-events",
            json={
                "date": datetime.date.today().strftime("%Y-%m-%d") + " 0:0:0",
                "template_id": self.template_id,
                "data": {
                    "name": name,
                    "amount": price
                }
            },
            headers=self._get_basic_headers(),
            cookies={
                "jwt": auth_token
            }
        )
        if response.status_code != 200:
            raise UserError(
                f"Purchase data has not been sent, code:{response.status_code}")

    def get_last_entries(self):
        auth_token = self._ensure_auth()
        response = requests.get(
            url=f"{self.api_url}/api/data/{self.template_id}/day-events",
            headers=self._get_basic_headers(),
            cookies={
                "jwt": auth_token
            }
        )
        if response.status_code != 200:
            raise UserError(
                f"Last purchase data has not been received, code:{response.status_code}"
            )

        last_entries = ""
        for i in range(len(response.json())):
            last_entries += f'{response.json()[i]["data"]["name"]}: {response.json()[i]["data"]["amount"]}\n'

        return last_entries.rstrip()

    def _authorize(self) -> str:
        response = requests.post(
            url=f"{self.api_url}/api/user/login_check",
            json={
                "_username": self.app_username,
                "_password": self.app_password
            },
            headers=self._get_basic_headers()
        )
        if response.status_code != 200:
            raise UserError(
                f'Authorization failed, code: {response.status_code}')

        return response.cookies.get("jwt")

    def _ensure_auth(self) -> str:
        if self._jwt_token:
            decoded = jwt.decode(self._jwt_token, options={
                                 "verify_signature": False})
            if decoded["exp"] < (time.time() + 60):
                self._jwt_token = self._authorize()
        else:
            self._jwt_token = self._authorize()

        return self._jwt_token

    def _get_basic_auth_token(self) -> str:
        auth_data = f"{self.basic_username}:{self.basic_password}".encode(
            "ascii")
        base64_bytes = base64.b64encode(auth_data)
        base64_string = base64_bytes.decode("ascii")

        return base64_string

    def _get_basic_headers(self) -> dict:
        return {
            "Authorization": "Basic " + self._get_basic_auth_token(),
            "Content-Type": "application/json"
        }
