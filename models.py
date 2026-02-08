from dataclasses import dataclass

from pydantic import BaseModel


@dataclass
class RawRecipe:
    title: str
    ingredients: list[str]
    instructions: str
    source_url: str


class Ingredient(BaseModel):
    name: str
    quantity: str
    note: str


class Bowl(BaseModel):
    label: str
    explanation: str
    ingredients: list[Ingredient]


class BowledRecipe(BaseModel):
    title: str
    source_url: str
    bowls: list[Bowl]
    method_steps: list[str]
