from django.test import TestCase
from ira.service.lexer import Lexer, Token, TokenType
from ira.service.parser import Parser


class ParserTestCase(TestCase):
    def setUp(self):
        self.lexer: Lexer = Lexer()
        self.parser: Parser = Parser()
