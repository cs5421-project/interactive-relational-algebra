from typing import List, Optional

from ira.model.token import Token
from ira.constants import *


class Lexer:
    """
    To tokenize the string values into understandable tokens
    """

    def __init__(self):
        # TODO: Deprecate this  constant definitions in favour of constants module.
        self.reserved_tokens = {
            SELECT: TokenType.SELECT, PROJECTION: TokenType.PROJECTION, UNION: TokenType.UNION,
            NATURAL_JOIN: TokenType.NATURAL_JOIN, "=": TokenType.EQUALS,
            AND: TokenType.AND, OR: TokenType.OR, NOT: TokenType.NOT, ARROW: TokenType.ARROW,
            PRODUCT: TokenType.PRODUCT, DIFFERENCE: TokenType.DIFFERENCE, DIVISION: TokenType.DIVISION,
            CARTESIAN:TokenType.CARTESIAN, INTERSECTION: TokenType.INTERSECTION,
            ANTI_JOIN: TokenType.ANTI_JOIN
        }

        self.unary_tokens = {
            TokenType.SELECT, TokenType.PROJECTION, TokenType.RENAME
        }

        self.brackets = {
            "(": TokenType.OPEN_PARENTHESIS, ")": TokenType.CLOSED_PARENTHESIS
        }

    def tokenize(self, input: str):
        """
        Tokenize the input into known tokens
        Assumptions: One line of input and the expression is correct
        """
        tokens = []
        cur_ident = ""
        for ch in input:
            # Check if it is the end of an indentifier, which could be a whitespace or an operator
            if self.is_end_of_ident(ch):
                if len(cur_ident) > 0:
                    tokens.append(self.get_literal_token(cur_ident))

                # Add the token for a reserved keyword
                if ch in self.reserved_tokens:
                    tokens.append(Token(ch, self.reserved_tokens[ch]))
                cur_ident = ""
            elif ch in self.brackets:  # Tokenize parenthesised expressions
                if len(cur_ident) > 0:
                    tokens.append(self.get_literal_token(cur_ident))
                    cur_ident = ""
                # Add the bracket in the tokens
                tokens.append(Token(ch, self.brackets[ch]))
            # Identify if it is an IDENT token or DIGIT token
            elif not self.is_same_type(cur_ident, ch):
                if len(cur_ident) > 0:
                    tokens.append(self.get_literal_token(cur_ident))
                cur_ident = ch
            else:  # Append the characters to get a word
                cur_ident += ch
                if cur_ident in self.reserved_tokens:
                    tokens.append(
                        Token(cur_ident, self.reserved_tokens[cur_ident]))
                    cur_ident = ""
        if len(cur_ident) > 0:
            tokens.append(self.get_literal_token(cur_ident))
        tokens = self.combine_py_expressions(tokens)
        return tokens

    def combine_py_expressions(self, tokens: List[Token]):
        new_tokens = []
        while len(tokens) > 0:
            if tokens[0].type in self.unary_tokens:  # Unary operators
                op = tokens[0]
                tokens = tokens[1:]  # Remove operator from the tokens

                if tokens[0].type == TokenType.OPEN_PARENTHESIS:
                    parenthesis_end = self.find_parenthesis_position(tokens,
                                                                     '(', self.find_matching_parenthesis(tokens))
                else:
                    parenthesis_end = self.find_parenthesis_position(tokens, '(')

                if parenthesis_end == -1:
                    raise Exception(
                        '( could not be found in a unary operation')
                attributes = tokens[:parenthesis_end]
                new_tokens.append(Token(op.value, op.type, attributes))
                tokens = tokens[parenthesis_end:]  # Removing parameter from the tokens
            else:
                new_tokens.append(tokens[0])
                tokens = tokens[1:]
        return new_tokens

    def is_end_of_ident(self, ch):
        return ch in self.reserved_tokens or ch == " "

    def get_literal_token(self, cur_ident):
        if cur_ident.isalnum() and cur_ident.isnumeric():
            return (Token(cur_ident, TokenType.DIGIT))
        else:
            return (Token(cur_ident, TokenType.IDENT))


    def is_same_type(self, cur_ident, ch):
        if cur_ident.isnumeric() and not ch.isnumeric():
            return False

        return True

    def find_matching_parenthesis(self, tokens: List[Token], start=0) -> Optional[int]:
        '''Finds the ending bracket which matches the opening bracket'''
        # Count of open brackets
        count = 0
        for i in range(start, len(tokens)):
            if tokens[i].type == TokenType.OPEN_PARENTHESIS:
                count += 1
            elif tokens[i].type == TokenType.CLOSED_PARENTHESIS:
                count -= 1

            if count < 0:
                raise Exception("Too many ) in the expression")
            if count == 0:
                return i  # position of the correct closing parenthesis
        return None

    def find_parenthesis_position(self, tokens: List[Token], token_value: str, start: int = 0) -> int:
        '''
        Find at which position the token_value exists
        '''
        r = -1
        for i in range(start, len(tokens)):
            if tokens[i:][0].value == (token_value):
                return i
        return r


def display_tokens(tokens: List[Token]):
    for token in tokens:
        print(token)
