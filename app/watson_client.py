from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson import AssistantV2


@dataclass
class WatsonAssistantClient:
    """Small stateful wrapper around the IBM watsonx Assistant v2 SDK."""

    service_url: str
    assistant_id: str
    environment_id: str
    api_key: str

    @classmethod
    def from_environment(cls) -> "WatsonAssistantClient":
        values = {
            "service_url": os.getenv("WATSON_ASSISTANT_URL", "").strip(),
            "assistant_id": os.getenv("WATSON_ASSISTANT_ID", "").strip(),
            "environment_id": os.getenv("WATSON_ASSISTANT_ENVIRONMENT_ID", "").strip(),
            "api_key": os.getenv("WATSON_ASSISTANT_API_KEY", "").strip(),
        }
        missing = [name for name, value in values.items() if not value]
        if missing:
            raise RuntimeError(
                "Missing Watson Assistant configuration: " + ", ".join(missing)
            )
        return cls(**values)

    def _service(self) -> AssistantV2:
        authenticator = IAMAuthenticator(self.api_key)
        service = AssistantV2(version="2024-08-25", authenticator=authenticator)
        service.set_service_url(self.service_url)
        return service

    def create_session(self) -> str:
        response = self._service().create_session(
            assistant_id=self.assistant_id,
            environment_id=self.environment_id,
        ).get_result()
        session_id = response.get("session_id")
        if not session_id:
            raise RuntimeError("Watson Assistant did not return a session_id")
        return session_id

    def send_message(self, session_id: str, message: str) -> dict[str, Any]:
        result = self._service().message(
            assistant_id=self.assistant_id,
            environment_id=self.environment_id,
            session_id=session_id,
            input={"message_type": "text", "text": message},
        ).get_result()
        return result

    @staticmethod
    def text_from_response(result: dict[str, Any]) -> list[str]:
        messages = result.get("output", {}).get("generic", [])
        return [
            item["text"]
            for item in messages
            if item.get("response_type") == "text" and item.get("text")
        ]
