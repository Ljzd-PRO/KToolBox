from typing import Type, Any

from pydantic import BaseModel, field_serializer

from ktoolbox import __version__

__all__ = ["BaseKToolBoxData"]


class BaseKToolBoxData(BaseModel):
    """
    Base class for all KToolBox data models.
    """
    def __init__(self, **data: Any):
        super().__init__(**data)
        self.type = type(self)

    version: str = __version__
    type: Type["BaseKToolBoxData"] = None

    @field_serializer('type')
    def _(self, value: Type["BaseKToolBoxData"], _info):
        return str(value)
