
import pytest
import os
from app.config import Config


def test_chunk_values():
    assert Config.CHUNK_OVERLAP < Config.CHUNK_SIZE
    assert Config.CHUNK_SIZE > 0
    
def test_validate():
    original_key = Config.GOOGLE_API_KEY
    Config.GOOGLE_API_KEY = ""
    
    with pytest.raises(EnvironmentError, match="GOOGLE_API_KEY is not set. Add it to your .env file or Render dashboard."):
        Config.validate()
    
    Config.GOOGLE_API_KEY = original_key
    
    


@pytest.mark.parametrize("config_attr", [
    "GOOGLE_API_KEY",
    "GEMINI_MODEL",
    "EMBEDDING_MODEL",
    "MAX_TOKENS",
    "TEMPERATURE"
])

def test_config_values(config_attr):
    # Use getattr to look up the value of the attribute by its string name
    value = getattr(Config, config_attr)
    
    # Assert that the value exists and is not an empty string or None
    assert value is not None, f"{config_attr} should not be None"
    assert value != "", f"{config_attr} should not be an empty string"