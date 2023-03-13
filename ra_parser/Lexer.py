import enum
from typing import List


class TokenType(enum.Enum):
    SELECT = 0
    PROJECT = 1
    UNION = 2
    DIFFERENCE = 3
    CARTESIAN = 4
    RENAME = 5
    NATURAL_JOIN = 6
    ANTI_JOIN = 7
    IDENT = 8
    EQUALS = 9
    AND = 10
    OR = 11
    NOT = 12
    OPEN_PARENTHESIS = 13
    CLOSED_PARENTHESIS = 14
    DIGIT = 15


class Token():

    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __eq__(self, __o: object) -> bool:
        return self.type == __o.type and self.value == __o.value

    def __str__(self):
        return f'Token is {self.value} of type {self.type}'


class Lexer:
    """
    To tokenize the string values into understandable tokens
    """

    def __init__(self):
        self.reserved_tokens = {
            "σ": TokenType.SELECT, "π": TokenType.PROJECT, "∪": TokenType.UNION, "⨝": TokenType.NATURAL_JOIN, "=": TokenType.EQUALS, "and": TokenType.AND, "or": TokenType.OR, "not": TokenType.NOT}

        self.brackets = {
            "(": TokenType.OPEN_PARENTHESIS, ")": TokenType.CLOSED_PARENTHESIS
        }

    def tokenize(self, input: str):
        """
        Tokenize the input into know tokens

        Assumptions: One line of input and the expression is correct
        """
        tokens = []
        cur_ident = ""
        for ch in input:
            if self.is_end_of_ident(ch):
                if len(cur_ident) > 0:
                    tokens.append(self.get_literal_token(cur_ident))
                if ch in self.reserved_tokens:
                    tokens.append(Token(ch, self.reserved_tokens[ch]))
                cur_ident = ""
            elif ch in self.brackets:
                if len(cur_ident) > 0:
                    tokens.append(self.get_literal_token(cur_ident))
                    cur_ident = ""
                tokens.append(Token(ch, self.brackets[ch]))
            elif not self.is_same_type(cur_ident, ch):
                if len(cur_ident) > 0:
                    tokens.append(self.get_literal_token(cur_ident))
                cur_ident = ch
            else:
                cur_ident += ch
                if cur_ident in self.reserved_tokens:
                    tokens.append(
                        Token(cur_ident, self.reserved_tokens[cur_ident]))
                    cur_ident = ""
        if len(cur_ident) > 0:
            tokens.append(self.get_literal_token(cur_ident))
        return tokens

    def is_end_of_ident(self, ch):
        return ch in self.reserved_tokens or ch == " "

    def get_literal_token(self, cur_ident):
        if cur_ident.isalnum() and not cur_ident.isnumeric():
            return (Token(cur_ident, TokenType.IDENT))
        else:
            return (Token(cur_ident, TokenType.DIGIT))

    def is_same_type(self, cur_ident, ch):
        if cur_ident.isnumeric() and not ch.isnumeric():
            return False

        return True


def display_tokens(tokens: List[Token]):
    for token in tokens:
        print(token)
