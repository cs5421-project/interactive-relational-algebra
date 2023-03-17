from typing import List

from ira.constants import TokenType, LOGICAL_OPERATORS, COMPARATIVE_OPERATORS
from ira.model.query import Query
from ira.service.lexer import Token
from ira.service.util import is_unary_operator, split_string

QUERY_MAPPER = {TokenType.SELECT: "select * from {table_name} where {conditions};",
                TokenType.PROJECTION: "select {column_names} from {table_name};"}


def transform(parsed_postfix_tokens: List[Token]) -> Query:
    # TODO: Add support for other operators and other complex scenario etc
    # TODO: Do validation and further sanitation while parsing and not here
    stack = []
    while parsed_postfix_tokens:
        token = parsed_postfix_tokens.pop()

        operands = []
        number_of_operands = 1 if is_unary_operator(token.type) else 2
        for _ in range(number_of_operands):
            operands.append(parsed_postfix_tokens.pop())

        if token.type == TokenType.SELECT:
            conditions = sanitise(str(token.attributes), token.type)
            query = QUERY_MAPPER[token.type].format(table_name=operands[0].value, conditions=conditions)
            stack.append(query)

        elif token.type == TokenType.PROJECTION:
            column_names = sanitise(str(token.attributes), token.type)
            query = QUERY_MAPPER[token.type].format(column_names=column_names, table_name=operands[0].value)
            stack.append(query)

    return Query(stack[0])


def sanitise(query_segment: str, token_type: TokenType):
    """
    Surrounding column name with " just in case if column name contain characters like "." etc
    """
    if token_type == TokenType.PROJECTION:
        return ",".join('"{column_name}"'.format(column_name=column_name)
                        for column_name in str(query_segment).split(','))
    elif token_type == TokenType.SELECT:
        conditions = split_string(query_segment, LOGICAL_OPERATORS)
        for condition in conditions:
            condition_segments = split_string(condition, COMPARATIVE_OPERATORS)
            column_name = condition_segments[0]
            query_segment = query_segment.replace(column_name, '"{column_name}"'
                                                  .format(column_name=column_name))
        return query_segment
