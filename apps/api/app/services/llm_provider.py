from typing import Protocol, Optional
from app.config import get_settings
from app.middleware.pii_masking import PIIMasker, contains_efirma_material


class LLMProvider(Protocol):
    def complete(self, messages: list[dict], model: Optional[str] = None) -> str: ...


class OpenAIProvider:
    def __init__(self, api_key: str):
        self._api_key = api_key

    def complete(self, messages: list[dict], model: Optional[str] = None) -> str:
        try:
            import openai
            client = openai.OpenAI(api_key=self._api_key)
            response = client.chat.completions.create(
                model=model or "gpt-4o",
                messages=messages,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"Error al comunicarse con OpenAI: {e}"


class AnthropicProvider:
    def __init__(self, api_key: str):
        self._api_key = api_key

    def complete(self, messages: list[dict], model: Optional[str] = None) -> str:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self._api_key)
            system_msg = ""
            filtered = []
            for m in messages:
                if m["role"] == "system":
                    system_msg = m["content"]
                else:
                    filtered.append(m)

            response = client.messages.create(
                model=model or "claude-sonnet-4-20250514",
                max_tokens=4096,
                system=system_msg,
                messages=filtered,
            )
            return response.content[0].text
        except Exception as e:
            return f"Error al comunicarse con Anthropic: {e}"


class SafeLLMProvider:
    def __init__(self, provider: LLMProvider):
        self._provider = provider
        self._masker = PIIMasker()

    def complete(self, messages: list[dict], model: Optional[str] = None) -> str:
        for msg in messages:
            if contains_efirma_material(msg.get("content", "")):
                raise ValueError(
                    "Material de e.firma detectado en el mensaje. "
                    "Nunca se envía material criptográfico a proveedores de IA."
                )

        masked_messages = []
        for msg in messages:
            masked_messages.append({
                **msg,
                "content": self._masker.mask(msg.get("content", "")),
            })

        response = self._provider.complete(masked_messages, model)
        return self._masker.unmask(response)


def get_llm_provider() -> SafeLLMProvider:
    settings = get_settings()
    if settings.llm_provider == "anthropic":
        base = AnthropicProvider(settings.anthropic_api_key)
    else:
        base = OpenAIProvider(settings.openai_api_key)
    return SafeLLMProvider(base)
