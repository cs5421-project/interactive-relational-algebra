from typing import List, Optional, Tuple

from ira.model.token import Token
from ira.constants import *


class Lexer:
    """
    To tokenize the string values into understandable tokens
    """

    def __init__(self):
        self.reserved_tokens = {
            **UNARY_OPERATORS_TO_TOKEN_TYPE, **BINARY_OPERATORS_TO_TOKEN_TYPE,
            **COMPARATIVE_OPERATORS_TO_TOKEN_TYPE
        }

        self.unary_tokens = {
            **UNARY_OPERATORS_TO_TOKEN_TYPE
        }

        self.brackets = {
            OPEN_PARENTHESIS: TokenType.OPEN_PARENTHESIS, CLOSED_PARENTHESIS: TokenType.CLOSED_PARENTHESIS
        }

    def tokenize(self, input: str):
        """
        Tokenize the input into known tokens
        Assumptions: One line of input and the expression is correct
        """
        tokens = []
        cur_ident = ""
        length_of_input = len(input)
        index = 0
        while index < length_of_input:
            ch = input[index]
            # Check if it is the end of an identifier, which could be a whitespace or an operator
            if self.is_end_of_ident(ch):
                if len(cur_ident) > 0:
                    tokens.append(self.get_literal_token(cur_ident))
                #  Checking for <= and >=
                if ch in (LESSER_THAN, GREATER_THAN):
                    if index + 1 < length_of_input:
                        if input[index + 1] == EQUALS:
                            ch += EQUALS
                            index += 1

                # Add the token for a reserved keyword
                if ch in self.reserved_tokens:
                    tokens.append(Token(ch, self.reserved_tokens[ch]))
                cur_ident = ""
            elif ch in self.brackets:  # Tokenize parenthesised expressions
                if len(cur_ident) > 0:
                    tokens.append(self.get_literal_token(cur_ident))
                    cur_ident = ""
                # Add the bracket in the tokens
                tokens.append(Token(ch, self.brackets[ch]))
            # Identify if it is an IDENT token or DIGIT token
            elif not self.is_same_type(cur_ident, ch):
                if len(cur_ident) > 0:
                    tokens.append(self.get_literal_token(cur_ident))
                cur_ident = ch
            else:  # Append the characters to get a word
                cur_ident += ch
                if cur_ident in self.reserved_tokens:
                    tokens.append(
                        Token(cur_ident, self.reserved_tokens[cur_ident]))
                    cur_ident = ""
            index += 1
        if len(cur_ident) > 0:
            tokens.append(self.get_literal_token(cur_ident))
        tokens = self.post_process(tokens)
        return tokens

    def post_process(self, tokens: List[Token]):
        new_tokens = []
        while len(tokens) > 0:
            current_token = tokens[0]
            current_token_type = current_token.type
            if current_token_type in self.unary_tokens:  # Unary operators
                tokens = tokens[1:]  # Remove operator from the tokens

                if tokens[0].type == TokenType.OPEN_PARENTHESIS:
                    parenthesis_end = self.find_parenthesis_position(tokens,
                                                                     '(', self.find_matching_parenthesis(tokens))
                else:
                    parenthesis_end = self.find_parenthesis_position(tokens, '(')

                if parenthesis_end == -1:
                    raise Exception(
                        '( could not be found in a unary operation')
                attributes = tokens[:parenthesis_end]
                new_tokens.append(Token(current_token.value, current_token_type, attributes))
                tokens = tokens[parenthesis_end:]  # Removing parameter from the tokens
            elif current_token_type in (TokenType.LEFT_JOIN, TokenType.RIGHT_JOIN,
                                        TokenType.NATURAL_JOIN, TokenType.FULL_JOIN, TokenType.SELECT,
                                        TokenType.PROJECTION):
                attributes = self.get_subsequent_attributes(tokens)
                if attributes:
                    new_tokens.append(Token(current_token.value, current_token_type, attributes))
                    # +1 to account for current_token
                    tokens = tokens[len(attributes) + 1:]
                else:
                    new_tokens.append(tokens[0])
                    tokens = tokens[1:]
            else:
                new_tokens.append(tokens[0])
                tokens = tokens[1:]
        return new_tokens

    def is_end_of_ident(self, ch):
        return ch == " " or ch in self.reserved_tokens

    def get_literal_token(self, cur_ident):
        if cur_ident.isalnum() and cur_ident.isnumeric():
            return (Token(cur_ident, TokenType.DIGIT))
        else:
            return (Token(cur_ident, TokenType.IDENT))

    def is_same_type(self, cur_ident, ch):
        if cur_ident.isnumeric() and not ch.isnumeric():
            return False
        return True

    def find_matching_parenthesis(self, tokens: List[Token], start=0) -> Optional[int]:
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

    def find_parenthesis_position(self, tokens: List[Token], token_value: str, start: int = 0) -> int:
        '''
        Find at which position the token_value exists
        '''
        r = -1
        for i in range(start, len(tokens)):
            if tokens[i:][0].value == (token_value):
                return i
        return r

    def get_subsequent_attributes(self, tokens: List[Token]) -> List[Token]:
        previous_token_type = tokens[0]
        tokens = tokens[1:]
        attributes = []
        parenthesis_stack = []
        length_of_tokens = len(tokens)
        if length_of_tokens == 1:
            # For scenario in which there is ideally an identifier after an operator with attribute capability,
            # there is no attributes to store, hence return nothing
            return attributes
        for current_token_index in range(length_of_tokens):
            current_token = tokens[current_token_index]
            current_token_type = current_token.type
            if current_token_type == TokenType.OPEN_PARENTHESIS:
                # 2nd argument in the below list keeps track of whether there
                # has been any logical or comparative operator starting from a certain open parenthesis
                parenthesis_stack.append([current_token_index, False])
            elif current_token_type == TokenType.CLOSED_PARENTHESIS:
                if parenthesis_stack:
                    parenthesis_index, is_logical_comparative_operator_persisted = parenthesis_stack.pop()
                    if not is_logical_comparative_operator_persisted:
                            return attributes[:parenthesis_index]
                else:
                    raise Exception("Syntactical exception; Found a closed parenthesis before an open parenthesis")
            elif current_token_type == TokenType.IDENT and previous_token_type == TokenType.IDENT:
                if parenthesis_stack:
                    raise Exception("Syntactical exception; Found open brackets which does not close properly "
                                    "before end of condition")
                return attributes
            elif previous_token_type in (*LOGICAL_OPERATORS_TOKEN_TYPE, *COMPARATIVE_OPERATORS_TOKEN_TYPE):
                if parenthesis_stack:
                    # Updating logical or comparative operator for the most recent open parenthesis
                    parenthesis_stack[-1][-1] = True
                if current_token_type not in (TokenType.IDENT, TokenType.DIGIT):
                    raise Exception("Syntactical exception; Require an identifier or a digit after a logical operator")
            elif current_token_type not in (TokenType.OPEN_PARENTHESIS, TokenType.CLOSED_PARENTHESIS,
                                            TokenType.DIGIT, TokenType.IDENT, TokenType.EQUALS,
                                            *LOGICAL_OPERATORS_TOKEN_TYPE, *COMPARATIVE_OPERATORS_TOKEN_TYPE):
                # If it reaches here, it implies that token_type is not a logical operator as well.
                if parenthesis_stack:
                    return attributes[:parenthesis_stack[0][0]]
                return attributes
            previous_token_type = current_token_type
            attributes.append(current_token)
        if not attributes:
            raise Exception("Syntactical exception; Got an operator followed by nothing..")
        return attributes


def display_tokens(tokens: List[Token]):
    for token in tokens:
        print(token)
