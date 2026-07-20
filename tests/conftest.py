from __future__ import annotations

from collections.abc import Iterator

import pytest

from ktoolbox.configuration import Configuration, config


@pytest.fixture(autouse=True)
def restore_configuration() -> Iterator[None]:
    """Restore the mutable process-wide configuration after every test."""
    snapshot = config.model_copy(deep=True)
    yield
    for field_name in type(config).model_fields:
        setattr(config, field_name, getattr(snapshot, field_name))


@pytest.fixture
def isolated_configuration() -> Configuration:
    return Configuration(_env_file=None)
