"""Client HTTP isolé pour les applications Dify d'AidFinder."""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator, Mapping
from typing import Any

import requests

from app.core.config import DIFY_API_KEY, DIFY_API_URL, DIFY_USER

logger = logging.getLogger("aidfinder.dify_client")

DifyResult = dict[str, Any]


class DifyClient:
    """Encapsule les appels bloquants et SSE à l'API Dify.

    Le client ne participe à aucun workflow applicatif. Les services qui
    l'utiliseront ultérieurement reçoivent toujours un dictionnaire avec la
    clé ``success`` plutôt qu'une exception HTTP brute.
    """

    def __init__(self, timeout: int = 60) -> None:
        self.base_url = DIFY_API_URL.rstrip("/")
        self.api_key = DIFY_API_KEY
        self.user = DIFY_USER
        self.timeout = timeout

    def send_message(
        self,
        message: str,
        conversation_id: str | None = None,
        inputs: Mapping[str, Any] | None = None,
        user: str | None = None,
    ) -> DifyResult:
        """Envoie un message à Dify et retourne sa réponse bloquante.

        Args:
            message: Message utilisateur à transmettre à Dify.
            conversation_id: Identifiant de conversation Dify existant.
            inputs: Variables d'entrée attendues par l'application Dify.
            user: Identifiant utilisateur Dify. Par défaut, ``DIFY_USER``.
        """
        configuration_error = self._configuration_error(user)
        if configuration_error:
            return configuration_error

        logger.info("[Dify] Appel bloquant envoyé")
        try:
            response = requests.post(
                self._chat_messages_url,
                headers=self._headers,
                json=self._payload(
                    message=message,
                    response_mode="blocking",
                    conversation_id=conversation_id,
                    inputs=inputs,
                    user=user,
                ),
                timeout=self.timeout,
            )
        except requests.Timeout:
            logger.warning("[Dify] Timeout après %s secondes", self.timeout)
            return self._error("Dify request timed out.")
        except requests.RequestException as exc:
            logger.error("[Dify] Erreur réseau: %s", exc)
            return self._error("Unable to reach Dify.")
        except Exception:
            logger.exception("[Dify] Erreur inattendue pendant l'appel")
            return self._error("Unexpected Dify client error.")

        return self._parse_blocking_response(response)

    def send_message_stream(
        self,
        message: str,
        conversation_id: str | None = None,
        inputs: Mapping[str, Any] | None = None,
        user: str | None = None,
    ) -> Iterator[DifyResult]:
        """Diffuse les évènements SSE Dify sous forme de résultats cohérents.

        Chaque élément produit contient ``success``. Les évènements de message
        conservent également leur contenu Dify dans ``raw`` et leur texte dans
        ``answer``. Une erreur réseau, HTTP ou de décodage produit un unique
        élément d'échec, sans laisser remonter d'exception brute.
        """
        configuration_error = self._configuration_error(user)
        if configuration_error:
            yield configuration_error
            return

        logger.info("[Dify] Appel streaming envoyé")
        try:
            with requests.post(
                self._chat_messages_url,
                headers=self._headers,
                json=self._payload(
                    message=message,
                    response_mode="streaming",
                    conversation_id=conversation_id,
                    inputs=inputs,
                    user=user,
                ),
                timeout=self.timeout,
                stream=True,
            ) as response:
                if not response.ok:
                    yield self._http_error(response)
                    return

                for line in response.iter_lines(decode_unicode=True):
                    if not line or not line.startswith("data:"):
                        continue
                    yield self._parse_stream_event(line[5:].strip())

                logger.info("[Dify] Streaming terminé avec succès")
        except requests.Timeout:
            logger.warning("[Dify] Timeout streaming après %s secondes", self.timeout)
            yield self._error("Dify request timed out.")
        except requests.RequestException as exc:
            logger.error("[Dify] Erreur réseau streaming: %s", exc)
            yield self._error("Unable to reach Dify.")
        except Exception:
            logger.exception("[Dify] Erreur inattendue pendant le streaming")
            yield self._error("Unexpected Dify client error.")

    @property
    def _chat_messages_url(self) -> str:
        return f"{self.base_url}/chat-messages"

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _configuration_error(self, user: str | None) -> DifyResult | None:
        if not self.base_url:
            logger.error("[Dify] Configuration absente: DIFY_API_URL")
            return self._error("DIFY_API_URL is not configured.")
        if not self.api_key:
            logger.error("[Dify] Configuration absente: DIFY_API_KEY")
            return self._error("DIFY_API_KEY is not configured.")
        if not (user or self.user):
            logger.error("[Dify] Configuration absente: DIFY_USER")
            return self._error("DIFY_USER is not configured.")
        return None

    def _payload(
        self,
        message: str,
        response_mode: str,
        conversation_id: str | None,
        inputs: Mapping[str, Any] | None,
        user: str | None,
    ) -> dict[str, Any]:
        return {
            "inputs": dict(inputs or {}),
            "query": message,
            "response_mode": response_mode,
            "conversation_id": conversation_id or "",
            "user": user or self.user,
        }

    def _parse_blocking_response(self, response: requests.Response) -> DifyResult:
        if not response.ok:
            return self._http_error(response)

        try:
            payload = response.json()
        except (json.JSONDecodeError, requests.JSONDecodeError):
            logger.error("[Dify] Réponse JSON invalide")
            return self._error("Invalid JSON response from Dify.", response.status_code)

        if not isinstance(payload, dict):
            logger.error("[Dify] Réponse JSON inattendue")
            return self._error("Unexpected response format from Dify.", response.status_code)
        if payload.get("code") or payload.get("error"):
            logger.error("[Dify] Erreur retournée par Dify")
            return self._error(
                str(payload.get("message") or payload.get("error") or "Dify error."),
                response.status_code,
                payload,
            )

        logger.info("[Dify] Appel bloquant réussi")
        return self._success(payload)

    def _parse_stream_event(self, data: str) -> DifyResult:
        try:
            payload = json.loads(data)
        except json.JSONDecodeError:
            logger.error("[Dify] Évènement SSE JSON invalide")
            return self._error("Invalid JSON event from Dify.")

        if not isinstance(payload, dict):
            logger.error("[Dify] Évènement SSE inattendu")
            return self._error("Unexpected stream event from Dify.")
        if payload.get("event") == "error" or payload.get("code") or payload.get("error"):
            logger.error("[Dify] Erreur retournée pendant le streaming")
            return self._error(
                str(payload.get("message") or payload.get("error") or "Dify error."),
                raw=payload,
            )
        return self._success(payload)

    def _http_error(self, response: requests.Response) -> DifyResult:
        payload: dict[str, Any] | None = None
        try:
            decoded = response.json()
            if isinstance(decoded, dict):
                payload = decoded
        except (json.JSONDecodeError, requests.JSONDecodeError):
            pass

        logger.error("[Dify] Erreur HTTP %s", response.status_code)
        return self._error(
            str((payload or {}).get("message") or "Dify returned an HTTP error."),
            response.status_code,
            payload,
        )

    @staticmethod
    def _success(payload: dict[str, Any]) -> DifyResult:
        return {
            "success": True,
            "answer": payload.get("answer", ""),
            "conversation_id": payload.get("conversation_id", ""),
            "raw": payload,
        }

    @staticmethod
    def _error(
        message: str,
        status_code: int | None = None,
        raw: dict[str, Any] | None = None,
    ) -> DifyResult:
        result: DifyResult = {
            "success": False,
            "error": message,
            "status_code": status_code,
        }
        if raw is not None:
            result["raw"] = raw
        return result

    def chat(self, message: str, user: str = "anonymous") -> DifyResult:
        """Compatibilité temporaire avec l'ancien point d'entrée Dify."""
        return self.send_message(message=message, user=user)


dify_client = DifyClient()
