from ira.constants import OPEN_PARENTHESIS

SELECT = "SELECT"


class Query:

    def __init__(self, value):
        self.value = value
        self.is_dql = self._is_dql()

    def _is_dql(self):
        upper_case_value = self.value.upper()
        return upper_case_value.startswith(SELECT) or upper_case_value.startswith(OPEN_PARENTHESIS + SELECT)
