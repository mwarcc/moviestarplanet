from typing import Any

def proxy_to_be_used(instance: Any, proxy: str) -> str:
    """
    Determine the proxy to be used, prioritizing instance.proxy over the provided proxy.

    Args:
        instance (Any): The instance containing the proxy attribute.
        proxy (str): The provided proxy string.

    Returns:
        str: The proxy string to be used.
    """
    # Use instance.proxy if it's not None, otherwise use the provided proxy
    return instance.proxy if instance.proxy is not None else proxy


def fix_proxy(proxy: str) -> str | None:
    """
    Fix the format of the proxy string to ensure it starts with 'http://'.

    Args:
        proxy (str): The proxy string to fix.

    Returns:
        str | None: The fixed proxy string or None if proxy is None.
    """
    if proxy is None:
        return None

    if not proxy.startswith('http'):
        return 'http://' + proxy
    
    return proxy