from __future__ import annotations

import errno

import httpx
import pytest
from pydantic import BaseModel, ValidationError

from ktoolbox.api.errors import (
    PawchiveAuthenticationError,
    PawchiveHTTPError,
    PawchiveNotFoundError,
    PawchiveResponseValidationError,
    PawchiveTransportError,
)
from ktoolbox.failures import (
    FailureCode,
    FailureStage,
    StagedFailure,
    classify_failure,
    failure_from_http_status,
    failure_report,
    generic_failure,
)


class ResponseModel(BaseModel):
    tags: list[str]


def api_response(status: int) -> httpx.Response:
    request = httpx.Request("GET", "https://example.test/api/v1/posts")
    return httpx.Response(status, request=request)


def test_response_validation_failure_exposes_only_safe_contract_details() -> None:
    with pytest.raises(ValidationError) as caught:
        ResponseModel.model_validate({"tags": "private input"})
    error = PawchiveResponseValidationError("list_creator_posts", api_response(200), caught.value)

    failure = classify_failure(
        error,
        stage=FailureStage.job_generation,
        platform="fanbox",
        creator_id="creator",
    )

    assert failure.code is FailureCode.response_incompatible
    assert failure.stage is FailureStage.work_list
    assert failure.operation == "list_creator_posts"
    assert failure.fields == ["$.tags"]
    assert "private input" not in failure.model_dump_json()


@pytest.mark.parametrize(
    ("error", "code", "retryable"),
    [
        (
            PawchiveTransportError(
                "GET",
                httpx.URL("https://example.test/posts"),
                httpx.ConnectError("offline"),
            ),
            FailureCode.network,
            True,
        ),
        (
            PawchiveTransportError(
                "GET",
                httpx.URL("https://example.test/posts"),
                httpx.ReadTimeout("slow"),
            ),
            FailureCode.timeout,
            True,
        ),
        (PawchiveAuthenticationError(api_response(403)), FailureCode.permission_denied, False),
        (PawchiveNotFoundError(api_response(404)), FailureCode.resource_not_found, False),
        (PawchiveHTTPError(api_response(429)), FailureCode.rate_limited, True),
        (PawchiveHTTPError(api_response(503)), FailureCode.http_error, True),
        (httpx.ReadTimeout("slow"), FailureCode.timeout, True),
        (httpx.ConnectError("offline"), FailureCode.network, True),
        (PermissionError("private path"), FailureCode.permission_denied, False),
        (OSError(errno.ENOSPC, "disk path"), FailureCode.disk_full, False),
        (
            StagedFailure(FailureStage.index_write, PermissionError("private index")),
            FailureCode.permission_denied,
            False,
        ),
        (LookupError("private revision"), FailureCode.resource_not_found, False),
        (RuntimeError("private detail"), FailureCode.unknown, False),
    ],
)
def test_failure_classification_is_stable_and_value_free(
    error: Exception,
    code: FailureCode,
    retryable: bool,
) -> None:
    failure = classify_failure(error, stage=FailureStage.file_request, file_name="sample.bin")

    assert failure.code is code
    assert failure.retryable is retryable
    assert failure.file_name == "sample.bin"
    assert "private" not in failure.model_dump_json()
    if isinstance(error, StagedFailure):
        assert failure.stage is FailureStage.index_write


def test_http_result_generic_failure_and_report_are_bounded() -> None:
    limited = failure_from_http_status(429, stage=FailureStage.file_request, file_name="one.bin")
    missing = failure_from_http_status(404, stage=FailureStage.file_request, file_name="two.bin")
    generic = generic_failure(stage=FailureStage.job_generation, message="x" * 600)
    report = failure_report([limited, missing, generic] * 40, creator_failures=1, file_failures=2)

    assert limited.code is FailureCode.rate_limited
    assert missing.code is FailureCode.http_error
    assert len(generic.message) == 500
    assert len(report.items) == 100
    assert report.summary == "Task finished with 1 creator failures and 2 file failures"
