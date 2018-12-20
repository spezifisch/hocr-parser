import json
import os
import unittest
from bs4 import BeautifulSoup
from hocr_parser import parser


class BaseTestClass(unittest.TestCase):
    """Super class for all test cases"""

    @classmethod
    def setup_class(cls):
        """
        Sets up fixtures used during tests.
        Creates a parser instance and saves it in cls.document.
        Additionally, parses the hocr document again with BeautifulSoup and
        saves the result in cls.soup so the parsed document can later be
        checked against the original html.
        """
        own_dir = os.path.dirname(os.path.abspath(__file__))

        hocr_file = "output.tesseract.hocr"
        hocr_path = os.path.join(own_dir, "data", hocr_file)

        expected_values_file = hocr_file.rsplit(".", 1)[0] + ".expected.json"
        expected_values_path = os.path.join(own_dir, "data", expected_values_file)

        cls.document = parser.HOCRDocument(hocr_path, is_path=True)
        cls.soup = BeautifulSoup(open(hocr_path, "r").read(), "html.parser")
        cls.expected = json.loads(open(expected_values_path).read())

    def recursively_compare_tree_against_html(self, func):
        """
        Utility function for the common task of looping through the document
        and html trees and comparing the obj and html nodes to each other.

        Takes a comparator function as argument. Comparator functions receive
        the following keyword arguments when they get called:
        - obj: The current ocr object
        - node: The current node in the html tree


        Defines an inner function that takes obj, node, parent as arguments.
        The inner function executes the comparator function with its input
        arguments. Then it loops through the children, calling itself
        with the child nodes as arguments.

        The inner function is invoked with the root nodes.

        :param func: A function object. Comparator function that gets called
                     for each element on each level. The comparator function
                     receives the three previous arguments as keyword arguments
                     on invocation
        """
        def inner(obj, node):
            # invoke comparator function
            func(obj=obj, node=node)

            # no children, no recursion
            child_class = obj._child_node_class
            if not child_class:
                return

            # get html child nodes
            child_html_class = obj._child_node_class.HTML_CLASS
            html_children = node.find_all("", {"class": child_html_class})

            # same number of object children and html child nodes
            self.assertEqual(len(obj.children), len(html_children))

            # loop over children and call recursive compare on them
            for (child, html_child) in zip(obj.children, html_children):
                inner(
                    obj=child,
                    node=html_child,
                )

        # call inner() with root elements
        inner(obj=self.document, node=self.soup)


class TreeStructureTests(BaseTestClass):
    def test_child_node_classes(self):
        self.assertIs(parser.HOCRDocument._child_node_class, parser.Page)
        self.assertIs(parser.Page._child_node_class, parser.Area)
        self.assertIs(parser.Area._child_node_class, parser.Paragraph)
        self.assertIs(parser.Paragraph._child_node_class, parser.Line)
        self.assertIs(parser.Line._child_node_class, parser.Word)
        self.assertIs(parser.Word._child_node_class, None)

    def test_equivalency(self):
        """
        test_equivalency (test_hocr.TreeStructureTests)

        Recursively compares an obj against the html node and checks different
        aspects to see if the generated object and the html node are
        equivalent, i.e. the object was generated from this node and all
        information was parsed correctly.

        Tests:
        - same id
        - same html
        - parents have same id
        - same number of children
        - children have same ids
        """
        def compare_func(obj, node):
            # same id
            self.assertEqual(obj.id, node.get("id"))

            # same html
            # If obj is a HOCRDocument, we can't easily compare html since
            # this class saves the entire html document.
            # Causes problems during parent validation for Page objects.
            # page.parent is a HOCRDocument, page_node.parent is the <body> tag
            # of the html document.
            # For now, only validate html if obj is not a HOCRDocument
            if not obj.__class__.__name__ == "HOCRDocument":
                self.assertEqual(obj._hocr_html, node)

            # parents have same id (only for non-root elements)
            if not obj == self.document and not node == self.soup:
                self.assertEqual(obj.parent.id, node.parent.get("id"))

            # same number of children
            child_class = obj._child_node_class
            if not child_class:
                return
            child_nodes = node.find_all("", {"class": child_class.HTML_CLASS})

            self.assertEqual(
                obj.nchildren,
                len(child_nodes)
            )

            # children have same ids
            for (child_obj, child_node) in zip(obj.children, child_nodes):
                self.assertEqual(child_obj.id, child_node.get("id"))

        self.recursively_compare_tree_against_html(compare_func)

    def test_parent_link(self):
        """
        test_parent_link (test_hocr.TreeStructureTests)

        Recursively compares the parent node of the current obj
        to the parent element of the html node.

        Tests for parent-child link
        The parent object in obj.parent must contain obj in its
        children list.
        """
        def compare_func(obj, node):
            # no need to test for parents on root level of the tree
            if obj == self.document and node == self.soup:
                return

            # parent-child link. obj must be in obj.parent.children
            self.assertTrue(obj in obj.parent.children)

        self.recursively_compare_tree_against_html(compare_func)

    def test_child_link(self):
        """
        test_child_link (test_hocr.TreeStructureTests)

        Recursively compares the child elements of an object against the
        child nodes of the corresponding html node.

        Tests for parent-child link
        Child objects must have obj as their parent
        """
        def compare_func(obj, node):
            child_class = obj._child_node_class
            if not child_class:
                return
            child_nodes = node.find_all("", {"class": child_class.HTML_CLASS})

            for (child_obj, child_node) in zip(obj.children, child_nodes):
                # parent-child link (children must have obj as their parent)
                self.assertEqual(child_obj.parent, obj)

        self.recursively_compare_tree_against_html(compare_func)


class HOCRParserTests(BaseTestClass):
    def test_creation_methods(self):
        """
        test_creation_methods (test_hocr.HOCRParserTests)

        The parser can be created in two ways: Either by instantiating
        HOCRDocument with a file path and is_path=False; or by instantiating
        HOCRDocument with a html string directly. Both methods should
        lead to the same parsed document.
        """
        doc1 = self.document
        doc2 = parser.HOCRDocument(self.soup.prettify(), is_path=False)
        self.assertEqual(doc1, doc2)

    def test_consistency(self):
        """
        test_consistency (test_ocr.HOCRParserTests)

        - number of children must be consistent
          obj.nchildren == len(obj._children)
                        == len(obj.children)

        - obj.html equals node.prettify()
        - coordinates
          obj.__coordinates == obj.coordinates == expected_coordinates
        """
        def compare_func(obj, node):
            # number of children must be consistent
            self.assertEquals(
                obj.nchildren,
                len(obj.children),
                len(obj._children)
            )

            # obj.html equals node.prettify()
            self.assertEqual(obj.html, node.prettify())

            # coordinates
            self.assertEquals(
                obj._HOCRElement__coordinates,
                obj.coordinates,
                self.expected["coordinates"][obj.id or "document"]
            )

        self.recursively_compare_tree_against_html(compare_func)

    def test_ocr_text(self):
        expected_text = self.expected["ocr_text"]

        def compare_func(obj, node):
            if obj.__class__.__name__ == "HOCRDocument":
                expected = expected_text["document"]
            else:
                expected = expected_text[obj.id]
            self.assertEqual(obj.ocr_text, expected)

        self.recursively_compare_tree_against_html(compare_func)

    def test_page_coordinates(self):
        pass








