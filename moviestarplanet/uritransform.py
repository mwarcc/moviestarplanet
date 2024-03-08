def match_(url: str, ensure_https: bool):
    """
    Replaces 'http://' with 'https://' in the given URL if ensure_https is True.
    
    Parameters:
        url (str): The URL to be modified.
        ensure_https (bool): If True, the URL will be modified to use 'https://' instead of 'http://'.
        
    Returns:
        str: The modified URL if ensure_https is True, otherwise returns the original URL.
    """
    if ensure_https:
        return str(url).replace('http://', 'https://')
    return str(url).replace('https://', 'http://')
