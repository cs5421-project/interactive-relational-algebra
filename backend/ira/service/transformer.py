from typing import List

from ira.model.query import Query
from ira.service.lexer import Token


def transform(parsed_postfix_tokens: List[Token]):
    while parsed_postfix_tokens:
        element = parsed_postfix_tokens.pop()

    return Query("select * from iris;")


def map_ra_query_operator_to_sql_operator(operator: str):
    # TODO
    pass
