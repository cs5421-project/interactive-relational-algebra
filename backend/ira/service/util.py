from typing import List

from ira.constants import *
from ira.constants import BINARY_OPERATOR_MAP, UNARY_OPERATOR_MAP


def is_binary_operator(token_type: TokenType):
    return token_type in BINARY_OPERATOR_MAP


def is_unary_operator(token_type: TokenType):
    return token_type in UNARY_OPERATOR_MAP


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
