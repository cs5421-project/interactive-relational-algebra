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
                <select>
                <attributes>
                    a=10
                </attributes>
                <query>
                    <parenthesis>
                    <relation>
                        R
                    </relation>
                    </parenthesis>
                </query>
                </select>
            </ra_expression>
            """
        self.assertEqual(self.compare_xmls(tree, expected), True)

        input = "σa1=10(R22)"
        tokens = self.lexer.tokenize(input)
        xml = convert_tokenized_ra_to_xml(tokens)
        tree = xml.get_tree()
        expected = """\
            <ra_expression>
                <select>
                <attributes>
                    a1=10
                </attributes>
                <query>
                    <parenthesis>
                    <relation>
                        R22
                    </relation>
                    </parenthesis>
                </query>
                </select>
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
          <natural_join>
            <relation>
                RTable
            </relation>
            <relation>
                STable
            </relation>
          </natural_join>
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
              <anti_join>
                <relation>
                  R
                </relation>
                <relation>
                  S
                </relation>
              </anti_join>
            </ra_expression>
            """
        self.assertEqual(self.compare_xmls(tree, expected), True)

    # def test_unions_to_xml(self):
    #     input = "A ∪ B ∪ C"
    #     tokens = self.lexer.tokenize(input)
    #     xml = convert_tokenized_ra_to_xml(tokens)
    #     tree = xml.get_tree()
    #     print(tree)

    def test_simple_project(self):
        input = "π name,age (A)"
        tokens = self.lexer.tokenize(input)
        xml = convert_tokenized_ra_to_xml(tokens)
        tree = xml.get_tree()
        expected = """\
            <ra_expression>
                <projection>
                    <attributes>
                        name,age
                    </attributes>
                    <query>
                        <parenthesis>
                            <relation>
                                A
                            </relation>
                        </parenthesis>
                    </query>
                </projection>
            </ra_expression>
            """
        self.assertEqual(self.compare_xmls(tree, expected), True)
