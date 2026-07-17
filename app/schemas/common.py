import re
from typing import Annotated

from pydantic import AfterValidator, Field

NAME_PATTERN = re.compile(r"^[a-z0-9_-]{3,64}$")


def validate_name(v: str) -> str:
    if not NAME_PATTERN.match(v):
        raise ValueError(
            "Name must be 3-64 chars, lowercase ASCII, digits, underscore, or hyphen."
        )
    return v


NameStr = Annotated[
    str, Field(min_length=3, max_length=64), AfterValidator(validate_name)
]
OptionalNameStr = Annotated[
    str | None,
    Field(min_length=3, max_length=64, default=None),
    AfterValidator(validate_name),
]
