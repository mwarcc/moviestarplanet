import random
from typing import Optional
from moviestarplanet.entities import RandomCredentials

def get_random_account_credentials(file_path: str, has_server: bool) -> RandomCredentials:
    """
    Retrieve random account credentials from a file.
    
    Args:
        file_path (str): The path to the file containing account credentials.
        has_server (bool): Indicates whether the credentials include server information.

    Returns:
        RandomCredentials: A named tuple containing the random account credentials.

    Raises:
        FileNotFoundError: If the specified file does not exist.
    """
    with open(file_path, 'r') as file:
        lines = [line.rstrip().split(':') for line in file]

    chosen_line = random.choice(lines)
    
    username, password = chosen_line[:2]
    server = chosen_line[3] if has_server else None
    return RandomCredentials(username=username, password=password, server=server)