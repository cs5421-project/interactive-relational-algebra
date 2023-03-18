from typing import List

from ira.constants import TokenType, LOGICAL_OPERATORS, COMPARATIVE_OPERATORS
from ira.model.query import Query
from ira.model.token import Token
from ira.service.util import split_string

QUERY_MAPPER = {TokenType.SELECT: "select * from {{}} where {conditions};",
                TokenType.PROJECTION: "select {column_names} from {{}};",
                TokenType.NATURAL_JOIN: "select * from {} natural join {};",
                TokenType.IDENT: "select * from {table_name};"}


def transform(parsed_postfix_tokens: List[Token]) -> Query:
    # TODO: Add support for other operators
    # TODO: Do validation and further sanitation while parsing and not here
    query_stack = []
    while parsed_postfix_tokens or query_stack:
        current_token = parsed_postfix_tokens.pop()
        if current_token.type == TokenType.IDENT and len(parsed_postfix_tokens) == 0:
            return generate_query(query_stack, current_token)
        elif current_token.type == TokenType.IDENT and query_stack:
            parent_token = query_stack[-1][-1]
            if parent_token:
                query_stack.append((None, current_token))
            else:
                raise Exception("RA query not well formed; Possible reason: binary operator ({{parent_token}}) not "
                                "getting 2 operands.".format(parent_token=parent_token))

        elif current_token.type == TokenType.SELECT:
            conditions = sanitise(str(current_token.attributes), current_token.type)
            query = QUERY_MAPPER[current_token.type].format(conditions=conditions)
            query_stack.append((query, None))

        elif current_token.type == TokenType.PROJECTION:
            column_names = sanitise(str(current_token.attributes), current_token.type)
            query = QUERY_MAPPER[current_token.type].format(column_names=column_names)
            query_stack.append((query, None))

        elif current_token.type == TokenType.NATURAL_JOIN:
            # TODO accept conditional attribute once tokenizer and parser allows it
            query = QUERY_MAPPER[current_token.type]
            query_stack.append((query, current_token))


def generate_query(query_stack, token):
    if query_stack:
        original_length_of_query_stack = len(query_stack)
        query, stored_query = process_query_stack(query_stack, token, 0, original_length_of_query_stack)
        while query_stack:
            is_top_level_query = len(query_stack) == 1
            if not is_top_level_query:
                query, stored_query = process_query_stack(query_stack, token, len(query_stack),
                                                          original_length_of_query_stack)
            else:
                stored_query, _ = query_stack.pop()
                query = "{}".format(stored_query.format(query))
        return Query(query)
    else:
        return Query(QUERY_MAPPER[TokenType.IDENT].format(table_name=token.value))


def process_query_stack(query_stack, token, level, original_length_of_query_stack):
    stored_query, sibling_token = query_stack.pop()
    if sibling_token:
        # If sibling token exists, then we are dealing with a binary operation here
        parent_query, _ = query_stack.pop()
        # Do not need an alias if it is a top level query
        level = None if original_length_of_query_stack == 2 else 0
        query = get_query_with_alias(parent_query.format(token.value, sibling_token.value), level)
    else:
        # Unary operation
        query = get_query_with_alias(stored_query.format(token.value), level)
    return query, stored_query


def get_query_with_alias(query, level):
    """
    Adding alias as postgres must need alias for sub-queries
    """
    if level is not None:
        return "({}) as q{}".format(query.rstrip(';'), level)
    else:
        return query


def sanitise(query_segment: str, token_type: TokenType):
    """
    Surrounding column name with " just in case if column name contain characters like "." etc
    """
    # TODO: Deprecated this
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
