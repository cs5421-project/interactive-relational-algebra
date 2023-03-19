from ira.constants import LOGICAL_OPERATORS, COMPARATIVE_OPERATORS
from ira.enum.token_type import TokenType
from ira.service.util import split_string


class Attributes:
    def __init__(self, parent_token, value):
        self.parent_token = parent_token
        self.value = value
        self.column_names = self.get_column_names()

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, Attributes) and \
            self.value == __o.value and self.column_names == __o.column_names

    def __str__(self):
        result = ""
        for token in self.value:
            if token.value in LOGICAL_OPERATORS:
                result += " "
            result += token.value
            if token.value in LOGICAL_OPERATORS:
                result += " "
        if result.startswith('(') and result.endswith(')'):
            result = result[1:-1]
        return result.strip()

    def get_column_names(self):
        if self.parent_token.type == TokenType.PROJECTION:
            return str(self).split(',')
        elif self.parent_token.type == TokenType.SELECT:
            # Selection
            conditions = split_string(str(self), LOGICAL_OPERATORS)
            column_names = []
            for condition in conditions:
                condition_segments = split_string(
                    condition, COMPARATIVE_OPERATORS)
                column_name = condition_segments[0]
                column_names.append(column_name)
            return column_names
