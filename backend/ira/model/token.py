from ira.model.attributes import Attributes


class Token:

    def __init__(self, value, type, attributes=None):
        self.value = value
        self.type = type
        self.attributes = Attributes(self, attributes) if attributes is not None else None

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, Token) and \
            self.type == __o.type and self.value == __o.value and self.attributes == __o.attributes

    def __str__(self):
        return f'Token is {self.value} of type {self.type} with attribute {self.attributes}'
