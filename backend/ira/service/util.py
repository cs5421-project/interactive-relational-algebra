from typing import List

from ira.constants import *
from ira.service.parser import binary_operators, unary_operators

binary_operators_map = {value: key for key, value in binary_operators.items()}
unary_operators_map = {value: key for key, value in unary_operators.items()}

operator_map = {**binary_operators_map, **unary_operators_map}


def is_binary_operator(token_type: TokenType):
    return token_type in binary_operators_map


def is_unary_operator(token_type: TokenType):
    return token_type in unary_operators_map


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
