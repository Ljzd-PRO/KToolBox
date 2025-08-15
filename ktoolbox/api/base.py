from abc import ABC, abstractmethod
from typing import Literal, Generic, TypeVar, Optional, Callable
from urllib.parse import urlunparse

import httpx
import tenacity
from loguru import logger
from pydantic import BaseModel, ValidationError, RootModel
from tenacity import RetryCallState, wait_fixed, retry_if_result
from tenacity.stop import stop_base, stop_never, stop_after_attempt

from ktoolbox._enum import RetCodeEnum
from ktoolbox.configuration import config
from ktoolbox.utils import BaseRet, generate_msg

__all__ = ["APITenacityStop", "APIRet", "BaseAPI"]

_T = TypeVar('_T')


class APITenacityStop(stop_base):
    """APIs Stop strategies"""

    def __call__(self, retry_state: RetryCallState) -> bool:
        if config.api.retry_times is None:
            return stop_never(retry_state)
        else:
            return stop_after_attempt(config.api.retry_times)(retry_state)


def _retry_error_callback(state: RetryCallState) -> "APIRet":
    """
    Call after all reties failed
    :return Keep the origin return value
    """
    # noinspection SpellCheckingInspection
    logger.error(
        generate_msg(
            f"Kemono API call failed",
            ret=state.outcome.result(),
        )
    )
    return state.outcome.result()


def _retry(*args, **kwargs):
    """Wrap an API method with a new ``Retrying`` object"""
    wrapper = tenacity.retry(
        stop=APITenacityStop(),
        wait=wait_fixed(config.api.retry_interval),
        retry=retry_if_result(lambda x: not bool(x)),
        reraise=True,
        retry_error_callback=_retry_error_callback,
        **kwargs
    )
    if len(args) == 1 and callable(args[0]):
        return wrapper(args[0])
    else:
        return wrapper


class APIRet(BaseRet[_T]):
    """Return data model of API call"""
    pass


class BaseAPI(ABC, Generic[_T]):
    path: str = "/"
    method: Literal["get", "post"]
    extra_validator: Optional[Callable[[str], BaseModel]] = None
    client = httpx.AsyncClient(
        verify=config.ssl_verify,
        headers={"Accept": "text/css"},
        cookies={"session": config.api.session_key} if config.api.session_key else None
    )

    Response = BaseModel
    """API response model"""

    @classmethod
    def handle_res(cls, res: httpx.Response) -> APIRet[_T]:
        """Handle API response"""
        try:
            if cls.extra_validator:
                res_model = cls.extra_validator(res.text)
            else:
                res_model = cls.Response.model_validate_json(res.text)
        except (ValueError, ValidationError) as e:
            return APIRet(
                code=RetCodeEnum.JsonDecodeError if isinstance(e, ValueError) else RetCodeEnum.ValidationError,
                message=generate_msg(url=res.url, status_code=res.status_code, response=res.text),
                exception=e
            )
        else:
            data = res_model.root if isinstance(res_model, RootModel) else res_model
            return APIRet(data=data)

    @classmethod
    @_retry
    async def request(cls, path: str = None, **kwargs) -> APIRet[_T]:
        """
        Make a request to the API
        :param path: Fully initialed URL path
        :param kwargs: Keyword arguments of ``httpx._client.AsyncClient.request``
        """
        if path is None:
            path = cls.path
        url_parts = [config.api.scheme, config.api.netloc, f"{config.api.path}{path}", '', '', '']
        url = str(urlunparse(url_parts))
        try:
            res = await cls.client.request(
                method=cls.method,
                url=url,
                timeout=config.api.timeout,
                follow_redirects=True,
                **kwargs
            )
        except Exception as e:
            return APIRet(
                code=RetCodeEnum.NetWorkError,
                message=generate_msg(url=url),
                exception=e
            )
        else:
            return cls.handle_res(res)

    @classmethod
    @abstractmethod
    async def __call__(cls, *args, **kwargs) -> APIRet[Response]:
        """Function to call API"""
        ...
