from typing import List

from ira.service.util import is_binary_operator, is_unary_operator
from ira.constants import TOKEN_TYPE_OPERATORS
from ira.enum.token_type import TokenType
from ira.model.token import Token


TAG_NAME_MAPPER = {
    TokenType.SELECT: "select",
    TokenType.PROJECTION: "projection",
    TokenType.RENAME: "rename",
    TokenType.IDENT: "relation",
    TokenType.CARTESIAN: "cartesian_product",
    TokenType.UNION: "union",
    TokenType.INTERSECTION: "intersection",
    TokenType.DIFFERENCE: "difference",
    TokenType.NATURAL_JOIN: "natural_join",
    TokenType.ANTI_JOIN: "anti_join",
    TokenType.LEFT_JOIN: "left_join",
    TokenType.RIGHT_JOIN: "right_join",
    TokenType.FULL_JOIN: "full_join"
}


class XmlNode:
    def __init__(self, tag_name="", value=None):
        self.children = []
        self.tag_name = tag_name
        self.value = value

    def set_tag_name(self, token_type):
        self.tag_name = TAG_NAME_MAPPER[token_type]

    def add_child(self, child: object):
        self.children.append(child)

    def get_tree(self, indent=0):
        tree = ' '*indent + "<"+self.tag_name+">\n"
        if self.value != None:
            tree += ' '*(indent+2) + self.value + '\n'
        for child in self.children:
            tree += child.get_tree(indent + 2)

        tree += ' '*indent + "</" + self.tag_name + ">\n"
        return tree


def convert_tokenized_ra_to_xml(tokens: List[Token], tag_name="ra_expression"):
    cur_node = XmlNode(tag_name)
    if len(tokens) == 1:
        end_node = XmlNode(TAG_NAME_MAPPER[tokens[0].type], tokens[0].value)
        cur_node.add_child(end_node)
        return cur_node
    i = 0
    while i < len(tokens):
        if tokens[i].type == TokenType.OPEN_PARENTHESIS:
            end_parenthesis = find_matching_parenthesis(tokens, i)
            child_node = convert_tokenized_ra_to_xml(
                tokens[i+1:end_parenthesis], "parenthesis")
            cur_node.add_child(child_node)
            i = end_parenthesis + 1
        elif tokens[i].type == TokenType.IDENT:
            child_node = XmlNode(
                TAG_NAME_MAPPER[tokens[i].type], tokens[i].value)
            cur_node.add_child(child_node)
            i += 1
        elif is_binary_operator(tokens[i].type):
            child_node = XmlNode("binary_operator")
            child_node.add_child(XmlNode("operator", tokens[i].value))
            cur_node.add_child(child_node)
            i += 1
        elif is_unary_operator(tokens[i].type):
            child_node = XmlNode(
                "unary_operator")
            child_node.add_child(XmlNode("operator", tokens[i].value))
            child_node.add_child(
                XmlNode("attributes", str(tokens[i].attributes)))
            cur_node.add_child(child_node)
            i += 1
        else:
            raise Exception("Unidentifiable token in xml convertor")
    return cur_node


def find_query_end(tokens: List[Token], start):
    while start < len(tokens):
        if tokens[start].type == TokenType.OPEN_PARENTHESIS:
            end_parenthesis = find_matching_parenthesis(tokens)
            start = end_parenthesis + 1

        if tokens[start].type in TOKEN_TYPE_OPERATORS:
            return start

        start += 1
    return len(tokens)


def find_matching_parenthesis(tokens: List[Token], start=0):
    '''Finds the ending bracket which matches the opening bracket'''
    # Count of open brackets
    count = 0
    for i in range(start, len(tokens)):
        if tokens[i].type == TokenType.OPEN_PARENTHESIS:
            count += 1
        elif tokens[i].type == TokenType.CLOSED_PARENTHESIS:
            count -= 1

        if count < 0:
            raise Exception("Too many ) in the expression")
        if count == 0:
            return i  # position of the correct closing parenthesis
    return None
