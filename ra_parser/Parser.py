import enum
from Lexer import Token
from typing import List, Union, Dict
from Constants import *


class NodeType(enum.Enum):
    SELECT = 0
    PROJECT = 1
    RENAME = 2
    PRODUCT = 3
    DIFFERENCE = 4
    UNION = 5
    INTERSECTION = 6
    DIVISION = 7
    NATURAL_JOIN = 8
    JOIN_LEFT = 9
    JOIN_RIGHT = 10
    JOIN_FULL = 11
    VARIALBE = 12


binary_operators = {PRODUCT: NodeType.PRODUCT, DIFFERENCE: NodeType.DIFFERENCE, UNION: NodeType.UNION, INTERSECTION: NodeType.INTERSECTION, DIVISION: NodeType.DIVISION,
                    NATURAL_JOIN: NodeType.NATURAL_JOIN, JOIN_LEFT: NodeType.JOIN_LEFT, JOIN_RIGHT: NodeType.JOIN_RIGHT, JOIN_FULL: NodeType.JOIN_FULL}
unary_operators = {PROJECT: NodeType.PRODUCT,
                   SELECT: NodeType.SELECT, RENAME: NodeType.RENAME}


class QueryNode:
    """
    Base class of the nodes of the Query Tree generated from the 
    Relational Algebra Expressions
    """

    def __init__(self, name, type) -> None:
        self.name = name
        self.type = type

    def print_tree(self, level: int = 0) -> str:
        '''
        Returns a representation of the tree using indentation
        '''
        r = '  ' * level + self.name
        if self.name in unary_operators:
            r += '\t%s\n' % self.prop
            r += self.child.print_tree(level + 1)
        elif self.name in binary_operators:
            r += self.left.print_tree(level + 1)
            r += self.right.print_tree(level + 1)
        return '\n' + r


class Variable(QueryNode):
    """
    Variable Query Node for table name which are the leaf nodes
    of the Query Tree
    """

    def __init__(self, name, type) -> None:
        super().__init__(name, type)

    def get_variable_name(self) -> str:
        return self.name


class Binary(QueryNode):
    """
    Binary Operator Query Node containing the operator as the name 
    with left and right children signifiying the operands
    """

    def __init__(self, name, type, left, right) -> None:
        super().__init__(name, type)
        self.left = left
        self.right = right

    def get_left_child(self) -> QueryNode:
        return self.left

    def get_right_child(self) -> QueryNode:
        return self.right

    def get_operator_name(self) -> str:
        return self.name


class Unary(QueryNode):
    """
    Unary Operator Query Node containing the operator as the name 
    with left and right children signifiying the operands
    """

    def __init__(self, name, type, prop, child) -> None:
        super().__init__(name, type)
        self.prop = prop
        self.child = child

    def get_child(self) -> QueryNode:
        return self.child

    def get_operator_name(self) -> str:
        return self.name

    def get_projection_prop(self) -> List[str]:
        if self.type != NodeType.PROJECT:
            raise Exception(
                'Get projection prop not supported for the type: ' + self.type)
        return [i for i in self.prop.split(',')]

    def get_rename_prop(self) -> Dict[str, str]:
        '''
        Returns the dictionary that the rename operation wants
        '''
        if self.type != NodeType.RENAME:
            raise Exception(
                'Get rename prop not supported for the type: ' + self.type)
        r = {}
        for i in self.prop.split(','):
            q = i.split("➡")
            r[q[0]] = q[1]
        return r


class Parser:
    def __init__(self):
        self.name = "Parser"

    def parse(self, tokens: List[Union[Token, List[Token]]]):

        if len(tokens) == 0:
            raise Exception(('Failed to parse empty tokens'))

        while len(tokens) == 1 and isinstance(tokens[0], list):
            tokens = tokens[0]

        if len(tokens) == 1:
            return Variable(tokens[0].value, NodeType.VARIALBE)

        # Check for binary operators first from the right since right associative
        for i in range(len(tokens)-1, -1, -1):
            if not isinstance(tokens[i], Token):
                continue
            if tokens[i].value in binary_operators:
                if i == 0:
                    raise Exception(
                        "Expected left operand for " + tokens[i].value)
                if len(tokens[i+1:]) == 0:
                    raise Exception(
                        "Expected right operand for " + tokens[i].value)
                return Binary(tokens[i].value, binary_operators[tokens[i].value], self.parse(tokens[:i]), self.parse(tokens[i+1:]))

        for i in range(len(tokens)):
            if tokens[i].value in unary_operators:
                if len(tokens) <= i + 2:
                    raise Exception(
                        "Expected more tokens for " + tokens[i].value)
                elif len(tokens) > i + 3:
                    raise Exception(
                        "Too many expressions for " + tokens[i].value)

                return Unary(tokens[i].value, unary_operators[tokens[i].value], convert_to_py_expression(tokens[i+1]), self.parse(tokens[i+2]))

        raise Exception("Parser error at " + tokens[0].value)


def convert_to_py_expression(tokens: List[Token]) -> str:
    """
    Convert the tokens to a string of expressions
    """
    res = ""
    for token in tokens:
        if token.value in logical_operators:
            res += " "
        res += token.value
        if token.value in logical_operators:
            res += " "
    return res
