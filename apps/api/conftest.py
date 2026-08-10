import pytest


@pytest.fixture(autouse=True)
def reset_settings():
    from app.config import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
