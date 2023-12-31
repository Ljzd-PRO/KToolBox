from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["TestCliConf", "TestSettings", "settings"]


class TestCliConf(BaseModel):
    commit_hash_length: int = 40
    search_empty_text: str = "None"


class TestSettings(BaseSettings):
    """
    Test settings
    """
    cli_conf: TestCliConf = TestCliConf()

    # noinspection SpellCheckingInspection
    model_config = SettingsConfigDict(
        env_prefix='ktoolbox_test_',
        env_nested_delimiter='__',
        env_file='.env.test',
        env_file_encoding='utf-8'
    )


settings = TestSettings()
