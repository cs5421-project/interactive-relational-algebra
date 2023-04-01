from ira.model.attributes import Attributes


class Token:

    def __init__(self, value, type, attributes=None):
        self.value = value
        self.type = type
        self.attributes = Attributes(self, attributes) if attributes is not None else None
        self.sql_query = None
        self.post_fix_index = None
        # Note: These are tokens, deciphered in postfix order.
        self.left_child_token = None
        self.right_child_token = None
        self.parent_token = None

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, Token) and \
            self.type == __o.type and self.value == __o.value and self.attributes == __o.attributes

    def __str__(self):
        return f'Token is {self.value} of type {self.type} with attribute {self.attributes} ' \
               f'with query{self.sql_query} with post fix index {self.post_fix_index}'

    def initialise_for_transformer(self, sql_query, post_fix_index, parent_token):
        self.sql_query = sql_query
        self.post_fix_index = post_fix_index
        self.parent_token = parent_token
