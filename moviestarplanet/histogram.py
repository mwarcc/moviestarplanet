from secrets import token_hex
import base64

def get_session_id() -> str:
    """
    Generate a random session id
    """
    return base64.b64encode(token_hex(23).encode()).decode()