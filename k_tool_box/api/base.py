from abc import ABC, abstractmethod
from typing import Literal, Generic, TypeVar, Optional, Callable, Any
from urllib.parse import urlunparse

import httpx
import tenacity
from pydantic import BaseModel, ValidationError, RootModel
from tenacity import RetryCallState, wait_fixed, retry_if_result
from tenacity.stop import stop_base, stop_never, stop_after_attempt

from k_tool_box.configuration import config
from k_tool_box.enum import RetCodeEnum
from k_tool_box.utils import BaseRet


__all__ = ["APITenacityStop", "APIRet", "BaseAPI"]

_T = TypeVar('_T')


class APITenacityStop(stop_base):
    """APIs Stop strategies"""

    def __call__(self, retry_state: RetryCallState) -> bool:
        if config.api_retry_times is None:
            return stop_never(retry_state)
        else:
            return stop_after_attempt(config.api_retry_times)(retry_state)


class APIRet(BaseRet):
    """Return data model of API call"""
    pass


class BaseAPI(ABC, Generic[_T]):
    path: str = "/"
    method: Literal["get", "post"]
    extra_validator: Optional[Callable[[str], BaseModel]] = None

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
    def handle_res(cls, res: httpx.Response) -> APIRet[_T]:
        """Handle API response"""
        try:
            if cls.extra_validator:
                res_model = cls.extra_validator(res.text)
            else:
                res_model = cls.Response.model_validate_json(res.text)
        except (ValueError, ValidationError) as e:
            if isinstance(e, ValueError):
                return APIRet(
                    code=RetCodeEnum.JsonDecodeError.value,
                    message=str(e),
                    exception=e
                )
            elif isinstance(e, ValidationError):
                return APIRet(
                    code=RetCodeEnum.ValidationError.value,
                    message=str(e),
                    exception=e
                )
        else:
            data = res_model.root if isinstance(res_model, RootModel) else res_model
            return APIRet(data=data)

    @classmethod
    @retry
    async def request(cls, path: str = None, **kwargs) -> APIRet[_T]:
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
                code=RetCodeEnum.NetWorkError.value,
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
