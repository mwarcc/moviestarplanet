from moviestarplanet.exceptions import *

def requires_login(func):
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, 'ticket') or self.ticket is None:
            raise LoginException("User not logged in")
        return func(self, *args, **kwargs)
    return wrapper