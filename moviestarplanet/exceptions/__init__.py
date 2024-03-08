class LoginException(Exception):
    def __init__(self, message="User is not  loggedIn."):
        self.message = message
        super().__init__(self.message)

class MspConnexionError(Exception):
    def __init__(self, message="Could not connect to host."):
        self.message = message
        super().__init__(self.message)