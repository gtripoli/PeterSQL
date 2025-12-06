class ConnectionException(Exception):
    def __init__(self):
        self.message = "Unable to connect to the server"