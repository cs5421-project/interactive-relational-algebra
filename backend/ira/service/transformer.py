from typing import List

from ira.constants import TokenType, LOGICAL_OPERATORS, COMPARATIVE_OPERATORS
from ira.model.query import Query
from ira.service.lexer import Token
from ira.service.util import is_unary_operator, split_string, OPERATOR_MAP

QUERY_MAPPER = {TokenType.SELECT: "select * from {{}} where {conditions};",
                TokenType.PROJECTION: "select {column_names} from {{}};"}


def transform(parsed_postfix_tokens: List[Token]) -> Query:
    # TODO: Add support for other operators and other complex scenario etc
    # TODO: Do validation and further sanitation while parsing and not here
    query_stack = []
    while parsed_postfix_tokens or query_stack:
        token = parsed_postfix_tokens.pop()

        if token.type == TokenType.IDENT and query_stack:
            # Adding alias as postgres must need alias for sub-queries
            query = "({}) as q0".format(query_stack.pop().format(token.value).rstrip(';'))
            while query_stack:
                is_top_level_query = len(query_stack) == 1
                if not is_top_level_query:
                    query = "({}) as q{level}".format(query_stack.pop().format(query).rstrip(';'),level=len(query_stack))
                else:
                    query = "{}".format(query_stack.pop().format(query))
            return Query(query)
        elif token.type in OPERATOR_MAP:
            if token.type == TokenType.SELECT:
                conditions = sanitise(str(token.attributes), token.type)
                query = QUERY_MAPPER[token.type].format(conditions=conditions)
                query_stack.append(query)

            elif token.type == TokenType.PROJECTION:
                column_names = sanitise(str(token.attributes), token.type)
                query = QUERY_MAPPER[token.type].format(column_names=column_names)
                query_stack.append(query)


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
