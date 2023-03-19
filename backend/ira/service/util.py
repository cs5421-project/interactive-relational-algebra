from typing import List

from ira.constants import TOKEN_TYPE_TO_BINARY_OPERATOR, TOKEN_TYPE_TO_UNARY_OPERATOR
from ira.enum.token_type import TokenType


def is_binary_operator(token_type: TokenType):
    return token_type in TOKEN_TYPE_TO_BINARY_OPERATOR


def is_unary_operator(token_type: TokenType):
    return token_type in TOKEN_TYPE_TO_UNARY_OPERATOR


def split_string(string: str, delimiters: List):
    primary_delimiter = None
    for delimiter in delimiters:
        if delimiter in string:
            primary_delimiter = delimiter
    if not primary_delimiter:
        return [string]
    for delimiter in delimiters:
        string = string.replace(delimiter, delimiters[0])
    return string.split(delimiters[0])
