import requests

from app.core.config import DIFY_API_KEY, DIFY_API_URL


class DifyClient:
    def __init__(self):
        self.base_url = DIFY_API_URL
        self.api_key = DIFY_API_KEY

    def chat(self, message: str, user: str = "anonymous") -> dict:
        """
        Envoie un message à Dify et retourne la réponse JSON.
        """

        url = f"{self.base_url}/chat-messages"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "inputs": {},
            "query": message,
            "response_mode": "blocking",
            "conversation_id": "",
            "user": user,
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=60,
        )

        response.raise_for_status()

        return response.json()


dify_client = DifyClient()