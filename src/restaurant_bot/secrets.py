import threading

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

from restaurant_bot.config import KEY_VAULT_URL

_client = None
_client_lock = threading.Lock()
_cache: dict[str, str] = {}
_cache_lock = threading.Lock()


def _get_client() -> SecretClient:
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                _client = SecretClient(vault_url=KEY_VAULT_URL, credential=DefaultAzureCredential())
    return _client


def get_secret(name: str) -> str:
    if name not in _cache:
        with _cache_lock:
            if name not in _cache:
                _cache[name] = _get_client().get_secret(name).value
    return _cache[name]
