import json
from typing import Type, Any, List, Generic, TypeVar, Union, Dict

from pydantic import BaseModel

from ktoolbox import __version__

__all__ = ["BaseKToolBoxData", "SearchResult", "RootModel"]

_T = TypeVar("_T")


def _dump_type(obj: Dict[str, Any], *args, **kwargs):
    obj["type"] = str(obj["type"])
    return json.dumps(obj, *args, **kwargs)


class BaseKToolBoxData(BaseModel):
    """
    Base class for all KToolBox data models.
    """

    def __init__(self, **data: Any):
        super().__init__(**data)
        self.type = type(self)

    version: str = __version__
    type: Union[Type["BaseKToolBoxData"], str] = None

    class Config(BaseModel.Config):
        json_dumps = _dump_type


class SearchResult(BaseKToolBoxData, Generic[_T]):
    """Cli search result"""
    result: List[_T] = []


class RootModel(BaseModel, Generic[_T]):
    __root__: _T
