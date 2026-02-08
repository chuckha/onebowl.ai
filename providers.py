import os

import anthropic
import openai

from models import BowledRecipe


class AnthropicProvider:
    def __init__(self) -> None:
        key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. "
                "Add it to your .env file."
            )
        self._client = anthropic.Anthropic(api_key=key)

    def analyze(self, system: str, user_content: str) -> BowledRecipe:
        result = self._client.messages.parse(
            model="claude-sonnet-4-5-20250514",
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user_content}],
            output_format=BowledRecipe,
        )
        parsed = result.parsed_output
        if parsed is None:
            raise RuntimeError("Anthropic returned an empty response.")
        return parsed


class OpenAIProvider:
    def __init__(self) -> None:
        key = os.environ.get("OPENAI_API_KEY", "")
        if not key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. "
                "Add it to your .env file."
            )
        self._client = openai.OpenAI(api_key=key)

    def analyze(self, system: str, user_content: str) -> BowledRecipe:
        result = self._client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_content},
            ],
            response_format=BowledRecipe,
        )
        parsed = result.choices[0].message.parsed
        if parsed is None:
            raise RuntimeError("OpenAI returned an empty response.")
        return parsed
