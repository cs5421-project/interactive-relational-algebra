from functools import lru_cache
from typing import List

from ira.constants import TOKEN_TYPE_OPERATORS, TOKEN_TYPE_TO_UNARY_OPERATOR, TOKEN_TYPE_TO_BINARY_OPERATOR, AND, \
    QUERY_BINARY_OPERATORS_TO_TOKEN_TYPE, TOKEN_TYPE_TO_QUERY_BINARY_OPERATOR
from ira.enum.token_type import TokenType
from ira.model.attributes import Attributes
from ira.model.query import Query
from ira.model.token import Token
from ira.service.pre_populator import TABLE_TO_COLUMN_NAMES
from ira.service.util import is_unary_operator

NUMBER_OF_OPERANDS_UNDER_BINARY_OPERATOR = 2

N_JOIN_BASE_QUERY = ["select * from {{}} natural {join_type} join {{}};",
                     "select * from {{}} {join_type} join {{}} on {{conditions}};"]


def get_n_join_queries(join_type):
    return tuple(query.format(join_type=join_type) for query in N_JOIN_BASE_QUERY)


ANTI_JOIN_RIGHT_ALIAS = "cq1"

QUERY_MAPPER = {TokenType.SELECT: "select * from {{}} where {conditions};",
                TokenType.PROJECTION: "select distinct {column_names} from {{}};",
                TokenType.NATURAL_JOIN: "select * from {} natural join {};",
                TokenType.IDENT: "select * from {table_name};",
                TokenType.CARTESIAN: "select * from {} cross join {};",
                TokenType.UNION: "{} union {}",
                TokenType.INTERSECTION: "{} intersect {}",
                TokenType.DIFFERENCE: "{} except {}",
                TokenType.LEFT_JOIN: get_n_join_queries("left"),
                TokenType.RIGHT_JOIN: get_n_join_queries("right"),
                TokenType.FULL_JOIN: get_n_join_queries("full"),
                TokenType.ANTI_JOIN: "select * from {{}}  natural left join {{}} as {anti_join_right_alias}"
                                     " where {null_conditions};"}

BINARY_OPERATORS_NEEDING_IDENT_EXPANSION = (TokenType.DIFFERENCE, TokenType.UNION, TokenType.INTERSECTION)


# TODO: Iterative version
def get_common_columns_for_anti_join(parsed_postfix_tokens: List[Token], index, common_columns, binary_operator_stack):
    if index < 0:
        raise Exception("Relational query is wrongly formed; Binary operator is missing operands")
    if len(parsed_postfix_tokens) == 2:
        if parsed_postfix_tokens[0].type == TokenType.IDENT and parsed_postfix_tokens[1].type == TokenType.IDENT:
            return TABLE_TO_COLUMN_NAMES[parsed_postfix_tokens[0].value].intersection(
                TABLE_TO_COLUMN_NAMES[parsed_postfix_tokens[1].value])
        else:
            raise Exception("Relational query is wrongly formed; Binary operator is missing operands")
    current_token = parsed_postfix_tokens[index]
    if current_token.type == TokenType.IDENT:
        if index == 0:
            if len(binary_operator_stack) == 0 or (
                    len(binary_operator_stack) == 1 and binary_operator_stack[-1][-1] == 1):
                return TABLE_TO_COLUMN_NAMES[current_token.value], index
            else:
                raise Exception("Relational query is wrongly formed; Binary operator is missing operands")
        elif binary_operator_stack:
            stored_token, number_of_binary_operators_seen = binary_operator_stack[-1]
            if number_of_binary_operators_seen == 1:
                binary_operator_stack.pop()
                return TABLE_TO_COLUMN_NAMES[current_token.value], index
            else:
                binary_operator_stack[-1] = (stored_token, 1)
                right_side_operand_columns = TABLE_TO_COLUMN_NAMES[current_token.value]
                left_side_operand_common_column, left_side_index = get_common_columns_for_anti_join(
                    parsed_postfix_tokens, index - 1, common_columns,
                    binary_operator_stack)
                # if union  or difference or intersect prefer the left operand over the right  one, since the
                # assumption for this operator is that the number of columns are same and the column types are same.
                if stored_token.type in (TokenType.UNION, TokenType.DIFFERENCE, TokenType.INTERSECTION):
                    if len(left_side_operand_common_column) != len(right_side_operand_columns):
                        raise Exception("Relational query is wrongly formed; Operator: {token} is supposed to have the"
                                        " same number of columns".format(token=current_token))
                    return left_side_operand_common_column, left_side_index
                # if natural join or anti join use intersection.
                elif stored_token.type in (TokenType.NATURAL_JOIN, TokenType.ANTI_JOIN):
                    return right_side_operand_columns \
                        .intersection(left_side_operand_common_column), left_side_index

                # if other join, cross join
                return right_side_operand_columns.union(left_side_operand_common_column), left_side_index
    elif current_token.type in TOKEN_TYPE_TO_BINARY_OPERATOR:
        # Keeping track of token and the number of identifiers  yet to see
        binary_operator_stack.append((current_token, 2))
        if index == len(parsed_postfix_tokens) - 1:
            # Starting point of anti-join
            right, last_reached_index = get_common_columns_for_anti_join(parsed_postfix_tokens, index - 1,
                                                                         common_columns,
                                                                         binary_operator_stack)
            left, _ = get_common_columns_for_anti_join(parsed_postfix_tokens, last_reached_index - 1, common_columns,
                                                       binary_operator_stack)
            return left.intersection(right)
    elif current_token.type == TokenType.PROJECTION:
        return current_token.attributes.get_column_names()
    return get_common_columns_for_anti_join(parsed_postfix_tokens, index - 1, common_columns, binary_operator_stack)


def generate_null_condition_for_anti_join(common_column_names, alias):
    result = ""
    for index in range(len(common_column_names)):
        and_clause = AND if index + 1 != len(common_column_names) else ""
        result += alias + '."' + common_column_names[index] + '" = null ' + and_clause + " "
    return result


def transform(parsed_postfix_tokens: List[Token]) -> Query:
    # TODO: need to identify when to expand on an identifier
    #       ans: when it is the direct children of certain operators
    #            certain operators: union, intersection and difference
    #            -
    # Output: List of queries + tokens

    binary_operator_tracker = []
    index = len(parsed_postfix_tokens) - 1
    previous_token = None

    while index >= 0:
        current_token = parsed_postfix_tokens[index]
        current_token_type = current_token.type

        is_previous_token_unary = (previous_token is not None) and is_unary_operator(previous_token.type)

        if current_token_type == TokenType.IDENT:

            # Expanding IDENT to a query if needed
            if not is_previous_token_unary and binary_operator_tracker:
                parent_binary_token, number_of_binary_operators_seen_since_then = binary_operator_tracker[-1]
                parent_token = parent_binary_token
                if number_of_binary_operators_seen_since_then == NUMBER_OF_OPERANDS_UNDER_BINARY_OPERATOR:
                    parent_binary_token.right_child_token = current_token
                    binary_operator_tracker[-1][-1] = 1
                elif number_of_binary_operators_seen_since_then == 1:
                    parent_binary_token.left_child_token = current_token
                    binary_operator_tracker.pop()

            elif is_previous_token_unary :
                parent_token = previous_token

            elif len(parsed_postfix_tokens) == 1:
                return Query(QUERY_MAPPER[current_token_type].format(table_name=current_token.value))
            else:
                raise Exception("Logical error; Relational algebra query is not well formed.")

            current_token.initialise_for_transformer(QUERY_MAPPER[current_token_type]
                                                     .format(table_name=current_token.value),
                                                     index,
                                                     parent_token)
        else:
            current_token.post_fix_index = index
            
            if is_previous_token_unary:
                current_token.parent_token = previous_token
            elif previous_token and binary_operator_tracker:
                current_token.parent_token = binary_operator_tracker[-1][0]

            # Assigning children tokens relevant to the previous token
            if previous_token:
                if previous_token.right_child_token and not is_previous_token_unary:
                    previous_token.left_child_token = current_token
                else:
                    previous_token.right_child_token = current_token

            if current_token_type == TokenType.SELECT:
                conditions = sanitise(current_token.attributes, current_token.type)
                current_token.sql_query = QUERY_MAPPER[current_token.type].format(conditions=conditions)

            elif current_token == TokenType.PROJECTION:
                column_names = sanitise(current_token.attributes, current_token.type)
                current_token.sql_query = QUERY_MAPPER[current_token.type].format(column_names=column_names)

            elif current_token_type == TokenType.ANTI_JOIN:
                if current_token.attributes:
                    raise Exception("Logical error; Anti join implementation does not support conditional join")
                else:
                    common_column_names = get_common_columns_for_anti_join(parsed_postfix_tokens,
                                                                           len(parsed_postfix_tokens) - 1, {}, [])
                    if not common_column_names:
                        raise Exception(
                            "Logical error; There are no common columns for the relation/subquery for the anti join "
                            "operator")
                    null_conditions = generate_null_condition_for_anti_join(list(common_column_names),
                                                                            ANTI_JOIN_RIGHT_ALIAS)
                    current_token.sql_query = QUERY_MAPPER[current_token.type].format(null_conditions=null_conditions,
                                                                                      anti_join_right_alias=ANTI_JOIN_RIGHT_ALIAS)
                    binary_operator_tracker.append([current_token, NUMBER_OF_OPERANDS_UNDER_BINARY_OPERATOR])

            elif current_token_type in TOKEN_TYPE_TO_QUERY_BINARY_OPERATOR:
                query = QUERY_MAPPER[current_token.type]
                is_certain_join = current_token.type in (TokenType.LEFT_JOIN,
                                                         TokenType.RIGHT_JOIN,
                                                         TokenType.FULL_JOIN)
                if current_token.attributes and is_certain_join:
                    # If certain join operator has attributes, it implies that it is a type of conditional/equi join
                    conditions = sanitise(current_token.attributes, current_token.type)
                    query = query[-1].format("{}", "{}", conditions=conditions)
                elif is_certain_join:
                    query = query[0]

                current_token.sql_query = query
                if binary_operator_tracker:
                    binary_operator_tracker[-1][-1] = 1
                binary_operator_tracker.append([current_token, NUMBER_OF_OPERANDS_UNDER_BINARY_OPERATOR])

        previous_token = current_token
        index -= 1

    leaf_token = parsed_postfix_tokens[0]
    return generate_query(leaf_token)


def get_right_child_details(initial_leaf_token):
    pass


def get_left_child_details(root):
    pass


def generate_query(initial_leaf_token) -> Query:
    root, right_child_query = get_right_child_details(initial_leaf_token)
    left_child_query = get_left_child_details(root)

    initial_leaf_token.left_child_token
    pass


def get_query_with_alias(query, level):
    """
    Adding alias as postgres must need alias for sub-queries
    """
    if level is not None:
        return "({}) as q{}".format(query.rstrip(';'), level)
    else:
        return query


def sanitise(attributes: Attributes, token_type: TokenType):
    """
    Using quoted identifiers to avoid ambiguity.
    Surrounding column name with " just in case if column name contain characters like "." etc
    """
    if token_type == TokenType.PROJECTION:
        return ",".join('"{column_name}"'.format(column_name=column_name)
                        for column_name in attributes.get_column_names())
    elif token_type in (TokenType.SELECT, TokenType.NATURAL_JOIN,
                        TokenType.FULL_JOIN, TokenType.RIGHT_JOIN,
                        TokenType.LEFT_JOIN):
        query_segment = str(attributes)
        for column_name in attributes.column_names:
            query_segment = query_segment.replace(column_name, '"{column_name}"'
                                                  .format(column_name=column_name))
        return query_segment
