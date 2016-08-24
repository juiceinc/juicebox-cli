class Response:
    def __init__(self, status_code, json_return=None):
        self.status_code = status_code
        self._json = json_return

    def json(self):
        return self._json
