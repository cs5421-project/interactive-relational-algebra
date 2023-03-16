SELECT = "SELECT"


class Query:

    def __init__(self, value):
        self.value = value
        self.is_dql = self._is_dql()

    def _is_dql(self):
        return self.value.upper().startswith(SELECT)
