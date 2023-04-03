from typing import List

from ira.constants import TOKEN_TYPE_TO_BINARY_OPERATOR, AND, \
    TOKEN_TYPE_TO_QUERY_BINARY_OPERATOR
from ira.enum.token_type import TokenType
from ira.model.attributes import Attributes
from ira.model.query import Query
from ira.model.token import Token
from ira.service.pre_populator import TABLE_TO_COLUMN_NAMES
from ira.service.util import is_unary_operator

QUERY_SEMI_COLON = ';'

NUMBER_OF_OPERANDS_UNDER_BINARY_OPERATOR = 2

N_JOIN_BASE_QUERY = ("select * from {{}} natural {join_type} join {{}}",
                     "select * from {{}} {join_type} join {{}} on {{conditions}}")


def get_join_queries(join_type):
    return tuple(query.format(join_type=join_type) for query in N_JOIN_BASE_QUERY)


ANTI_JOIN_RIGHT_ALIAS = "cq{}"

CERTAIN_JOIN_TOKEN_TYPES = (TokenType.LEFT_JOIN, TokenType.RIGHT_JOIN, TokenType.FULL_JOIN, TokenType.NATURAL_JOIN)

SQL_JOIN_TOKEN_TYPE = (*CERTAIN_JOIN_TOKEN_TYPES, TokenType.ANTI_JOIN, TokenType.CARTESIAN)

QUERY_MAPPER = {TokenType.SELECT: "select * from {{}} where {conditions}",
                TokenType.PROJECTION: "select distinct {column_names} from {{}}",
                TokenType.NATURAL_JOIN: ("select * from {} natural join {}",
                                         "select * from {} natural join {} where {conditions}"),
                TokenType.IDENT: "select * from {table_name}",
                TokenType.CARTESIAN: "select * from {} cross join {}",
                TokenType.UNION: "{} union {}",
                TokenType.INTERSECTION: "{} intersect {}",
                TokenType.DIFFERENCE: "{} except {}",
                TokenType.LEFT_JOIN: get_join_queries("left"),
                TokenType.RIGHT_JOIN: get_join_queries("right"),
                TokenType.FULL_JOIN: get_join_queries("full"),
                TokenType.ANTI_JOIN: "select * from {{}}  natural left join {{}} as {anti_join_right_alias}"
                                     " where {null_conditions}"}

# Needs some special type of processing
SET_OPERATOR_TOKENS = (TokenType.DIFFERENCE, TokenType.UNION, TokenType.INTERSECTION)


def transform(parsed_postfix_tokens: List[Token]) -> Query:
    binary_operator_tracker = []
    index = len(parsed_postfix_tokens) - 1
    previous_token = None

    while index >= 0:
        current_token = parsed_postfix_tokens[index]
        current_token_type = current_token.type
        current_token.post_fix_index = index
        is_previous_token_unary = (previous_token is not None) and is_unary_operator(previous_token.type)

        if current_token_type == TokenType.IDENT:
            popped_binary_operator_tracker = None
            if not is_previous_token_unary and binary_operator_tracker:
                parent_token, popped_binary_operator_tracker = \
                    process_for_parent_binary_operator(binary_operator_tracker,
                                                       current_token)

            elif is_previous_token_unary:
                parent_token = previous_token
                # Right side is the default
                parent_token.right_child_token = current_token

            elif len(parsed_postfix_tokens) == 1:
                return Query(QUERY_MAPPER[current_token_type].format(table_name=current_token.value) + QUERY_SEMI_COLON)
            else:
                raise Exception("Logical error; Relational algebra query is not well formed.")

            query = get_query_for_identifier_token(current_token, parent_token)
            current_token.initialise_for_transformer(query, index, parent_token)

            is_ready_to_process_queries = (popped_binary_operator_tracker is not None) or is_previous_token_unary
            if is_ready_to_process_queries:
                process_queries(current_token)

        else:
            # Non identifier scenario

            # Assigning parent token to the current token and children tokens to the previous token
            if is_previous_token_unary:
                current_token.set_parent_token(previous_token)
                # Right is default for unary token
                previous_token.right_child_token = current_token
            elif previous_token and binary_operator_tracker:
                parent_token, popped_binary_operator_tracker = \
                    process_for_parent_binary_operator(binary_operator_tracker,
                                                       current_token)
                current_token.set_parent_token(parent_token)

            if current_token_type == TokenType.SELECT:
                conditions = sanitise(current_token.attributes, current_token.type)
                current_token.sql_query = QUERY_MAPPER[current_token.type].format(conditions=conditions)

            elif current_token_type == TokenType.PROJECTION:
                column_names = sanitise(current_token.attributes, current_token.type)
                current_token.sql_query = QUERY_MAPPER[current_token.type].format(column_names=column_names)

            elif current_token_type == TokenType.ANTI_JOIN:
                if current_token.attributes:
                    raise Exception("Logical error; Anti join implementation does not support conditional/equi join")
                else:
                    common_column_names, _ = \
                        get_common_columns_for_anti_join(parsed_postfix_tokens[:index],
                                                         index - 1, {}, [])
                    if not common_column_names:
                        raise Exception(
                            "Logical error; There are no common columns for the relation/subquery for the anti join "
                            "operator")
                    anti_join_alias = ANTI_JOIN_RIGHT_ALIAS.format(index)
                    null_conditions = generate_null_condition_for_anti_join(list(common_column_names),
                                                                            anti_join_alias)
                    current_token.sql_query = QUERY_MAPPER[current_token.type].format(null_conditions=null_conditions,
                                                                                      anti_join_right_alias=anti_join_alias)
                    binary_operator_tracker.append([current_token, NUMBER_OF_OPERANDS_UNDER_BINARY_OPERATOR])

            elif current_token_type in TOKEN_TYPE_TO_QUERY_BINARY_OPERATOR:
                query = QUERY_MAPPER[current_token_type]

                is_token_join = current_token.type in CERTAIN_JOIN_TOKEN_TYPES
                if current_token.attributes and is_token_join:
                    # If join operator has attributes, it implies that it is a type of conditional/equi join
                    conditions = sanitise(current_token.attributes, current_token.type)
                    query = query[-1].format("{}", "{}", conditions=conditions)
                elif is_token_join:
                    query = query[0]

                current_token.sql_query = query
                if binary_operator_tracker:
                    binary_operator_tracker[-1][-1] = 1
                binary_operator_tracker.append([current_token, NUMBER_OF_OPERANDS_UNDER_BINARY_OPERATOR])

        previous_token = current_token
        index -= 1

    root_token = parsed_postfix_tokens[-1]
    return Query(root_token.sql_query + QUERY_SEMI_COLON)


def process_for_parent_binary_operator(binary_operator_tracker, current_token):
    popped_binary_operator_tracker = None
    parent_binary_token, number_of_operators_seen = binary_operator_tracker[-1]
    parent_token = parent_binary_token
    if number_of_operators_seen == NUMBER_OF_OPERANDS_UNDER_BINARY_OPERATOR:
        parent_binary_token.right_child_token = current_token
        binary_operator_tracker[-1][-1] = 1
    elif number_of_operators_seen == 1:
        parent_binary_token.left_child_token = current_token
        popped_binary_operator_tracker = binary_operator_tracker.pop()
    return parent_token, popped_binary_operator_tracker


def get_query_for_identifier_token(current_token, parent_token):
    if parent_token.type in SET_OPERATOR_TOKENS:
        query = QUERY_MAPPER[current_token.type].format(table_name=current_token.value)
    else:
        query = current_token.value
    return query


def process_queries(token):
    """ Forms and stores queries starting from a leaf token all the till the processed binary token"""
    current_token = token
    while current_token.parent_token:
        parent_token = current_token.parent_token
        is_query_formation_successful = form_query(parent_token)
        if not is_query_formation_successful:
            break
        current_token = parent_token


def form_query(token) -> bool:
    """ Takes in a parent token and form a query at that token level"""
    token_type = token.type
    is_right_child_available = token.right_child_token is not None
    is_left_child_available = token.left_child_token is not None
    left_query_value = None
    right_query_value = None
    if is_left_child_available:
        left_query_value = get_query_with_alias(token.left_child_token.sql_query, token.left_child_token.level,
                                                token.left_child_token.post_fix_index, token.type,
                                                token.left_child_token.type)

    if is_right_child_available:
        # Ignore for anti join as it comes with its own alias
        if token_type == TokenType.ANTI_JOIN:
            right_query_value = token.right_child_token.sql_query
        else:
            right_query_value = get_query_with_alias(token.right_child_token.sql_query,
                                                     token.right_child_token.level,
                                                     token.right_child_token.post_fix_index, token.type,
                                                     token.right_child_token.type)

    if is_unary_operator(token_type):
        if is_right_child_available:
            query_value = right_query_value
            token.sql_query = token.sql_query.format(query_value)
        else:
            return False

    elif token_type in (*CERTAIN_JOIN_TOKEN_TYPES, TokenType.CARTESIAN, *SET_OPERATOR_TOKENS, TokenType.ANTI_JOIN):
        if is_left_child_available and is_right_child_available:
            token.sql_query = token.sql_query.format(left_query_value, right_query_value)
        else:
            return False

    return True


def is_table_name(query):
    return query in TABLE_TO_COLUMN_NAMES


def get_query_with_alias(query, level, unique_identifier, parent_token_type, token_type):
    """
    Adding alias as postgres must need alias for sub-queries
    """
    if (level is not None or level == 0) and token_type != TokenType.IDENT:
        if parent_token_type in SQL_JOIN_TOKEN_TYPE or is_unary_operator(parent_token_type):
            return "({}) as q{}".format(query, unique_identifier)
        return "({})".format(query)
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


def get_common_columns_for_anti_join(parsed_postfix_tokens: List[Token], index, common_columns, binary_operator_stack):
    """Calculates the common columns between the operands of anti-join"""
    if index < 0:
        return set(), 0
    if len(parsed_postfix_tokens) == 2:
        if parsed_postfix_tokens[0].type == TokenType.IDENT and parsed_postfix_tokens[1].type == TokenType.IDENT:
            return TABLE_TO_COLUMN_NAMES[parsed_postfix_tokens[0].value].intersection(
                TABLE_TO_COLUMN_NAMES[parsed_postfix_tokens[1].value]), index
    current_token = parsed_postfix_tokens[index]
    if current_token.type == TokenType.IDENT:
        if index == 0:
            if len(binary_operator_stack) == 0 or (
                    len(binary_operator_stack) == 1 and binary_operator_stack[-1][-1] == 1):
                return TABLE_TO_COLUMN_NAMES[current_token.value], index
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
        binary_operator_stack.append((current_token, NUMBER_OF_OPERANDS_UNDER_BINARY_OPERATOR))
        if index == len(parsed_postfix_tokens) - 1:
            # Starting point of anti-join
            right, last_reached_index = get_common_columns_for_anti_join(parsed_postfix_tokens, index - 1,
                                                                         common_columns,
                                                                         binary_operator_stack)
            left, _ = get_common_columns_for_anti_join(parsed_postfix_tokens, last_reached_index , common_columns,
                                                       binary_operator_stack)
            return left.intersection(right), index
    elif current_token.type == TokenType.PROJECTION:
        return current_token.attributes.get_column_names()
    return get_common_columns_for_anti_join(parsed_postfix_tokens, index - 1, common_columns, binary_operator_stack)


def generate_null_condition_for_anti_join(common_column_names, alias):
    result = ""
    for index in range(len(common_column_names)):
        and_clause = AND if index + 1 != len(common_column_names) else ""
        result += alias + '."' + common_column_names[index] + '" is NULL ' + and_clause + " "
    return result.strip()
