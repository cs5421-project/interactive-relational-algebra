from django.test import TestCase
from ira.service.lexer import Lexer, Token, TokenType
from ira.service.xml_convertor import convert_tokenized_ra_to_xml
import xml.etree.ElementTree as ET


class XmlConverterTestCase(TestCase):
    def setUp(self):
        self.lexer: Lexer = Lexer()

    def compare_xmls(self, xml1: str, xml2: str):
        xml1 = xml1.replace(" ", "")
        xml2 = xml2.replace(" ", "")
        tree1 = ET.ElementTree(ET.fromstring(xml1))
        tree2 = ET.ElementTree(ET.fromstring(xml2))
        root1 = tree1.getroot()
        root2 = tree2.getroot()
        return ET.tostring(root1) == ET.tostring(root2)

    def test_simple_select_to_xml(self):
        input = "σa=10(R)"
        tokens = self.lexer.tokenize(input)
        xml = convert_tokenized_ra_to_xml(tokens)
        tree = xml.get_tree()
        expected = """\
            <ra_expression>
                <unary_operator>
                    <operator>
                        σ
                    </operator>
                    <attributes>
                        a=10
                    </attributes>
                </unary_operator>
                <parenthesis>
                    <relation>
                        R
                    </relation>
                </parenthesis>
            </ra_expression>
            """
        self.assertEqual(self.compare_xmls(tree, expected), True)

        input = "σa1=10(R22)"
        tokens = self.lexer.tokenize(input)
        xml = convert_tokenized_ra_to_xml(tokens)
        tree = xml.get_tree()
        expected = """\
            <ra_expression>
                <unary_operator>
                    <operator>
                        σ
                    </operator>
                    <attributes>
                        a1=10
                    </attributes>
                </unary_operator>
                <parenthesis>
                    <relation>
                        R22
                    </relation>
                </parenthesis>
            </ra_expression>
            """
        self.assertEqual(self.compare_xmls(tree, expected), True)

    def test_simple_join_to_xml(self):
        input = "RTable ⋈ STable"
        tokens = self.lexer.tokenize(input)
        xml = convert_tokenized_ra_to_xml(tokens)
        tree = xml.get_tree()
        expected = """\
        <ra_expression>
            <relation>
                RTable
            </relation>
            <binary_operator>
                <operator>
                    ⋈
                </operator>
            </binary_operator>
            <relation>
                STable
            </relation>
        </ra_expression>
        """
        self.assertEqual(self.compare_xmls(tree, expected), True)

    def test_simple_anti_join(self):
        input = "R ▷ S"
        tokens = self.lexer.tokenize(input)
        xml = convert_tokenized_ra_to_xml(tokens)
        tree = xml.get_tree()
        expected = """\
            <ra_expression>
            <relation>
                R
            </relation>
            <binary_operator>
                <operator>
                    ▷
                </operator>
            </binary_operator>
            <relation>
                S
            </relation>
            </ra_expression>
            """
        self.assertTrue(self.compare_xmls(tree, expected))

    def test_unions_to_xml(self):
        input = "(A ∪ B) ∪ C"
        tokens = self.lexer.tokenize(input)
        xml = convert_tokenized_ra_to_xml(tokens)
        tree = xml.get_tree()
        expected = """\
            <ra_expression>
              <parenthesis>
                <relation>
                    A
                </relation>
                <binary_operator>
                    <operator>
                        ∪
                    </operator>
                </binary_operator>
                <relation>
                    B
                </relation>
              </parenthesis>
                <binary_operator>
                    <operator>
                        ∪
                    </operator>
                </binary_operator>
                <relation>
                    C
                </relation>
            </ra_expression>
            """
        self.assertEqual(self.compare_xmls(tree, expected), True)

    def test_simple_project(self):
        input = "π name,age (A)"
        tokens = self.lexer.tokenize(input)
        xml = convert_tokenized_ra_to_xml(tokens)
        tree = xml.get_tree()

        expected = """\
            <ra_expression>
            <unary_operator>
                <operator>
                    π
                </operator>
                <attributes>
                    name,age
                </attributes>
            </unary_operator>
            <parenthesis>
                <relation>
                    A
                </relation>
            </parenthesis>
            </ra_expression>
            """
        self.assertEqual(self.compare_xmls(tree, expected), True)
