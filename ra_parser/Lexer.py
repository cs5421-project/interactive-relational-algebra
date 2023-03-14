import enum
from typing import List, Union, Optional
from Constants import *


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
    ARROW = 16


class Token():

    def __init__(self, value, type):
        self.value = value
        self.type = type

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
            SELECT: TokenType.SELECT, PROJECT: TokenType.PROJECT, UNION: TokenType.UNION, NATURAL_JOIN: TokenType.NATURAL_JOIN, "=": TokenType.EQUALS, AND: TokenType.AND, OR: TokenType.OR, NOT: TokenType.NOT, ARROW: TokenType.ARROW
        }

        self.unary_tokens = {
            TokenType.SELECT, TokenType.PROJECT, TokenType.RENAME
        }

        self.brackets = {
            "(": TokenType.OPEN_PARENTHESIS, ")": TokenType.CLOSED_PARENTHESIS
        }

    def convert_based_on_priority(self, tokens: List[Token]):
        """
        Modify the tokens generated after simple conversion of code to tokens to a
        list of Union(Token, List[Token]) based on the operator precedences
        """
        items: List[Union[Token, List[Token]]] = []
        while len(tokens) > 0:
            if tokens[0].type == TokenType.OPEN_PARENTHESIS:  # Parenthesis state
                end = self.find_matching_parenthesis(tokens)
                if end is None:
                    raise Exception('Missing matching \')\' in \'%s\'' %
                                    display_tokens(tokens))
                # Recursively convert parenthesis expressions
                items.append(self.convert_based_on_priority(tokens[1:end]))
                # Removes the entire parentesis and content from the tokens
                tokens = tokens[end + 1:]

            elif tokens[0].type in self.unary_tokens:  # Unary operators
                items.append(tokens[0])
                tokens = tokens[1:]  # Remove operator from the tokens

                if tokens[0].type == TokenType.OPEN_PARENTHESIS:
                    par = self.find_token(tokens,
                                          '(', self.find_matching_parenthesis(tokens))
                else:
                    par = self.find_token(tokens, '(')

                if par == -1:
                    raise Exception(
                        '( could not be found in a unary operantion')
                items.append(tokens[:par])
                tokens = tokens[par:]  # Removing parameter from the tokens
            else:  # Identifier or binary op
                items.append(tokens[0])
                tokens = tokens[1:]
        return items

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

    def find_matching_parenthesis(self, tokens: List[Token], start=0) -> Optional[int]:
        '''Finds the '''
        par_count = 0  # Count of parenthesis
        for i in range(start, len(tokens)):
            if tokens[i].type == TokenType.OPEN_PARENTHESIS:
                par_count += 1
            elif tokens[i].type == TokenType.CLOSED_PARENTHESIS:
                par_count -= 1
                if par_count == 0:
                    return i  # Closing parenthesis of the parameter
        return None

    def find_token(self, tokens: List[Token], token_value: str, start: int = 0) -> int:
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
