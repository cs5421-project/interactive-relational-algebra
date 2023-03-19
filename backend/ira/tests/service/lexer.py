from django.test import TestCase
from ira.service.lexer import Lexer, Token, TokenType


class LexerTestCase(TestCase):
    def setUp(self):
        self.lexer: Lexer = Lexer()

    def test_simple_select(self):
        input = "σa=10(R)"
        tokens = self.lexer.tokenize(input)
        attribute = [Token("a", TokenType.IDENT), Token(
            "=", TokenType.EQUALS), Token("10", TokenType.DIGIT)]
        expected = [Token("σ", TokenType.SELECT, attribute,),  Token(
            "(", TokenType.OPEN_PARENTHESIS), Token("R", TokenType.IDENT), Token(")", TokenType.CLOSED_PARENTHESIS)]
        self.assertListEqual(tokens, expected)

        input = "σa1=10(R22)"
        tokens = self.lexer.tokenize(input)
        attribute = [Token("a1", TokenType.IDENT), Token(
            "=", TokenType.EQUALS), Token("10", TokenType.DIGIT)]
        expected = [Token("σ", TokenType.SELECT, attribute), Token(
            "(", TokenType.OPEN_PARENTHESIS), Token("R22", TokenType.IDENT), Token(")", TokenType.CLOSED_PARENTHESIS)]
        self.assertListEqual(tokens, expected)

    def test_simple_join(self):
        input = "RTable ⋈ STable"
        tokens = self.lexer.tokenize(input)
        expected = [Token("RTable", TokenType.IDENT), Token(
            "⋈", TokenType.NATURAL_JOIN), Token("STable", TokenType.IDENT)]
        self.assertListEqual(tokens, expected)

    def test_simple_project(self):
        input = "π name,age (A)"
        tokens = self.lexer.tokenize(input)
        attribute = [Token("name,age", TokenType.IDENT)]
        expected = [Token("π", TokenType.PROJECTION, attribute), Token(
            "(", TokenType.OPEN_PARENTHESIS),
            Token("A", TokenType.IDENT), Token(")", TokenType.CLOSED_PARENTHESIS)]
        self.assertListEqual(tokens, expected)
