import os
from typing import Protocol

import config  # noqa: F401 — triggers load_dotenv()

from models import BowledRecipe, RawRecipe
from providers import AnthropicProvider, OpenAIProvider

SYSTEM_PROMPT = """\
You are a mise en place assistant. Your job is to reorganize recipe ingredients \
into "bowls" — groups of ingredients that are prepped together and added to the \
cooking vessel at the same moment.

A "bowl" is one physical prep container. Two ingredients belong in the same bowl \
only if they are added together with no cooking, waiting, or stirring in between. \
If the method says to cook, sauté, simmer, or wait before adding the next \
ingredient, that next ingredient must go in a separate bowl.

Rules:
- Every ingredient must appear in exactly one bowl. Do not skip or duplicate any.
- Each bowl gets a short descriptive label (e.g. "Dry Ingredients", "Sauce") \
and a one-sentence explanation of when/how the bowl is used in the method.
- Order the bowls in the sequence they are used during cooking.
- Method steps must be preserved exactly as written — do not rewrite them.
- If an ingredient is used across multiple steps, place it in the bowl for \
the step where it is first added.
- A single method step often describes a sequence of additions separated by \
cook times. Read carefully — each addition point is a separate bowl.
"""


class Provider(Protocol):
    def analyze(self, system: str, user_content: str) -> BowledRecipe: ...


class AnalyzeError(Exception):
    pass


_PROVIDERS: dict[str, type] = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
}


def get_provider() -> Provider:
    name = os.environ.get("AI_PROVIDER", "openai").lower()
    cls = _PROVIDERS.get(name)
    if cls is None:
        supported = ", ".join(sorted(_PROVIDERS))
        raise RuntimeError(
            f"Unknown AI_PROVIDER '{name}'. Supported: {supported}"
        )
    return cls()


def analyze_recipe(raw: RawRecipe) -> BowledRecipe:
    provider = get_provider()

    if raw.ingredients:
        user_content = _structured_message(raw)
    else:
        user_content = _fallback_message(raw)

    try:
        parsed = provider.analyze(SYSTEM_PROMPT, user_content)
    except Exception as exc:
        raise AnalyzeError(f"AI provider error: {exc}") from exc

    parsed.source_url = raw.source_url
    return parsed


def _structured_message(raw: RawRecipe) -> str:
    ingredients_text = "\n".join(f"- {ing}" for ing in raw.ingredients)
    return (
        f"Recipe: {raw.title}\n\n"
        f"Ingredients:\n{ingredients_text}\n\n"
        f"Method:\n{raw.instructions}"
    )


def _fallback_message(raw: RawRecipe) -> str:
    return (
        f"Below is raw text from a recipe page. Extract the title, ingredients, "
        f"and method steps, then organize the ingredients into bowls.\n\n"
        f"{raw.instructions}"
    )
