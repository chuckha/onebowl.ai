import anthropic

from config import get_api_key
from models import BowledRecipe, RawRecipe

SYSTEM_PROMPT = """\
You are a mise en place assistant. Your job is to reorganize recipe ingredients \
into "bowls" — groups of ingredients that are prepped and used together at the \
same point in the cooking method.

Rules:
- Every ingredient must appear in exactly one bowl. Do not skip or duplicate any.
- Each bowl gets a short descriptive label (e.g. "Dry Ingredients", "Sauce") \
and a one-sentence explanation of when/how the bowl is used in the method.
- Method steps must be preserved exactly as written — do not rewrite them.
- If an ingredient is used across multiple steps, place it in the bowl for \
the step where it is first added.
- Prefer fewer bowls when ingredients are used at the same time.
"""


class AnalyzeError(Exception):
    pass


def analyze_recipe(raw: RawRecipe) -> BowledRecipe:
    client = anthropic.Anthropic(api_key=get_api_key())

    if raw.ingredients:
        user_content = _structured_message(raw)
    else:
        user_content = _fallback_message(raw)

    try:
        result = client.messages.parse(
            model="claude-sonnet-4-5-20250514",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
            output_format=BowledRecipe,
        )
    except anthropic.APIError as exc:
        raise AnalyzeError(f"Claude API error: {exc}") from exc

    parsed = result.parsed_output
    if parsed is None:
        raise AnalyzeError("Claude returned an empty response.")

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
