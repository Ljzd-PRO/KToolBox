from abc import ABC, abstractmethod
from functools import cached_property
from json import JSONDecodeError
from pathlib import Path
from typing import Literal, Generic, TypeVar, Optional, Callable, Any
from urllib.parse import urlunparse

import httpx
import tenacity
from pydantic import BaseModel, ValidationError, ConfigDict
from tenacity import RetryCallState, wait_fixed, retry_if_result
from tenacity.stop import stop_base, stop_never, stop_after_attempt

from k_tool_box.configuration import config
from .enum import APIRetCodeEnum

__all__ = ["APITenacityStop", "APIRet", "BaseAPI"]

_T = TypeVar('_T')


class APITenacityStop(stop_base):
    """APIs Stop strategies"""
    def __call__(self, retry_state: RetryCallState) -> bool:
        if config.api_retry_times is None:
            return stop_never(retry_state)
        else:
            return stop_after_attempt(config.api_retry_times)(retry_state)


class APIRet(Generic[_T], BaseModel):
    """Return data model of API call"""
    code: int = APIRetCodeEnum.Success.value
    message: str = ''
    exception: Optional[Exception] = None
    data: Optional[_T] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __bool__(self):
        return self.code == APIRetCodeEnum.Success


class BaseAPI(ABC):
    path: str = "/"
    method: Literal["get", "post"]

    class Response(BaseModel):
        """
        API response model
        """
        pass

    @staticmethod
    def retry(*args, **kwargs):
        """Wrap a function with a new `Retrying` object"""
        wrapper = tenacity.retry(
            stop=APITenacityStop(),
            wait=wait_fixed(config.api_retry_interval),
            retry=retry_if_result(lambda x: not bool(x)),
            reraise=True,
            retry_error_callback=lambda x: x.outcome.result(),  # type: Callable[[RetryCallState], Any]
            **kwargs
        )
        if len(args) == 1 and callable(args[0]):
            return wrapper(args[0])
        else:
            return wrapper

    @classmethod
    def handle_res(cls, res: httpx.Response) -> APIRet[Response]:
        """Handle API response"""
        try:
            res_json = res.json()
        except JSONDecodeError as e:
            return APIRet(
                code=APIRetCodeEnum.JsonDecodeError.value,
                message=str(e),
                exception=e
            )
        else:
            try:
                return APIRet(
                    data=cls.Response.model_validate(res_json)
                )
            except ValidationError as e:
                return APIRet(
                    code=APIRetCodeEnum.ValidationError.value,
                    message=str(e),
                    exception=e
                )

    @classmethod
    @retry
    async def request(cls, path: str = None, **kwargs) -> APIRet[Response]:
        """
        Make a request to the API
        :param path: Fully initialed URL path
        :param kwargs: Keyword arguments of `httpx._client.AsyncClient.request`
        """
        if path is None:
            path = cls.path
        url_parts = [config.api_scheme, config.api_netloc, f"{config.api_path}{path}", '', '', '']
        url = urlunparse(url_parts)
        try:
            async with httpx.AsyncClient() as client:
                res = await client.request(
                    method=cls.method,
                    url=url,
                    timeout=config.api_timeout,
                    follow_redirects=True,
                    **kwargs
                )
        except Exception as e:
            return APIRet(
                code=APIRetCodeEnum.NetWorkError.value,
                message=str(e),
                exception=e
            )
        else:
            return cls.handle_res(res)

    @classmethod
    @abstractmethod
    async def __call__(cls, *args, **kwargs) -> APIRet[Response]:
        """Function to call API"""
        pass
