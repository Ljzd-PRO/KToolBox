from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

NonEmptyString = Annotated[str, StringConstraints(min_length=1)]
SearchQuery = Annotated[str, StringConstraints(min_length=3)]
Offset = Annotated[int, Field(ge=0, multiple_of=50)]
SHA256Hash = Annotated[str, StringConstraints(pattern=r"^[0-9a-fA-F]{64}$")]


class Parameters(BaseModel):
    """Strict base model for outgoing Pawchive parameters."""

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)


class PageParameters(Parameters):
    query: SearchQuery | None = Field(default=None, alias="q")
    offset: Offset | None = Field(default=None, alias="o")

    def query_parameters(self) -> dict[str, str | int]:
        parameters: dict[str, str | int] = {}
        if self.query is not None:
            parameters["q"] = self.query
        if self.offset is not None:
            parameters["o"] = self.offset
        return parameters


class CreatorParameters(Parameters):
    service: NonEmptyString
    creator_id: NonEmptyString


class CreatorPostListParameters(CreatorParameters, PageParameters):
    pass


class PostParameters(CreatorParameters):
    post_id: NonEmptyString


class FileHashParameters(Parameters):
    file_hash: SHA256Hash
