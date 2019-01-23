import json
import os
import unittest
from bs4 import BeautifulSoup
from bs4.element import NavigableString
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

        cls.document = parser.HOCRParser(hocr_path, is_path=True)
        cls.soup = BeautifulSoup(open(hocr_path, "r").read(), "html.parser")
        cls.expected = json.loads(open(expected_values_path).read())

    @staticmethod
    def get_children_of_node(node):

        def child_node_filter(node):
            if isinstance(node, NavigableString):
                return False
            if not node.has_attr("id"):
                return False

            return True

        return list(filter(child_node_filter, node.contents))

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

            # filter
            child_nodes = self.get_children_of_node(node)

            # same number of object children and html child nodes
            self.assertEqual(len(obj.children), len(child_nodes))

            # loop over children and call recursive compare on them
            for (child_obj, child_node) in zip(obj.children, child_nodes):
                inner(obj=child_obj, node=child_node)

        # call inner() with root elements
        inner(obj=self.document.root, node=self.soup.body)


class TreeStructureTests(BaseTestClass):
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
            self.assertEqual(obj.html.prettify, node.prettify)

            # parents have same id (only for non-root elements)
            if not obj == self.document.root:
                self.assertEqual(obj.parent.id, node.parent.get("id"))

            # same number of children
            child_nodes = self.get_children_of_node(node)
            self.assertEqual(len(obj.children), len(child_nodes))

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
            if obj == self.document.root:
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
            child_nodes = self.get_children_of_node(node)

            for (child_obj, child_node) in zip(obj.children, child_nodes):
                # parent-child link (children must have obj as their parent)
                self.assertEqual(child_obj.parent, obj)

        self.recursively_compare_tree_against_html(compare_func)


class HOCRParserTests(BaseTestClass):
    def test_parsing(self):
        # Strings next to other siblings shouldn't be parsed as nodes.
        html = BeautifulSoup("""
            <div id='node'>
                I am noise. Have some newlines.
                \n\n
                <p id='child'>I am content</p>
            </div>
        """, "html.parser")

        node = parser.HOCRNode(html.div)
        self.assertEqual(len(node.children), 1)
        self.assertEqual(node.ocr_text, "I am content")

        # Strings inside tags should be parsed as ocr_text but not as children
        html = BeautifulSoup("""
            <div id='node'>I am not noise</div>
        """, "html.parser")

        node = parser.HOCRNode(html.div)
        self.assertEqual(len(node.children), 0)
        self.assertEqual(node.ocr_text, "I am not noise")

        # tags without id should not be parsed
        html = BeautifulSoup("""
            <div id='node'>
                <p>I don't have an id</p>
                <p id='child'>I have an id</p>
            </div>
        """, "html.parser")

        node = parser.HOCRNode(html.div)
        self.assertEqual(len(node.children), 1)
        self.assertEqual(node.children[0].ocr_text, "I have an id")

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
                len(obj.children),
                len(obj._children)
            )

            # obj.html equals node
            self.assertEqual(obj._html, node)

            # coordinates
            self.assertEquals(
                obj._coordinates,
                obj.coordinates,
                self.expected["coordinates"][obj.id or "document"]
            )

            # confidence
            self.assertAlmostEqual(
                obj.confidence,
                self.expected["confidence"][obj.id or "document"]
            )

        self.recursively_compare_tree_against_html(compare_func)

    def test_ocr_text(self):
        expected_text = self.expected["ocr_text"]

        def compare_func(obj, node):
            if obj == self.document.root:
                expected = expected_text["document"]
            else:
                expected = expected_text[obj.id]
            self.assertEqual(obj.ocr_text, expected)

        self.recursively_compare_tree_against_html(compare_func)

    def test_page_coordinates(self):
        expected_coordinates = self.expected["coordinates"]

        def compare_func(obj, node):
            if obj == self.document.root:
                expected = expected_coordinates["document"]
            else:
                expected = expected_coordinates[obj.id]
            self.assertEqual(obj.coordinates, tuple(expected))

        self.recursively_compare_tree_against_html(compare_func)

    def test_creation_method_equality(self):
        doc1 = self.document
        doc2 = parser.HOCRParser(self.soup.prettify(), is_path=False)

        self.assertEqual(doc1.ocr_text, doc2.ocr_text)
