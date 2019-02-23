__author__ = 'Rafa Haro <rh@athento.com>'

import re
import sys
from bs4 import BeautifulSoup
from bs4.element import NavigableString

if sys.version_info < (3, 0):
    from io import open


COORDINATES_PATTERN = re.compile(
    r"\bbbox\s+(-?[0-9.]+)\s+(-?[0-9.]+)\s+(-?[0-9.]+)\s+(-?[0-9.]+)\b"
)

CHILD_STRING_SEPARATORS = {
    "ocr_page": "\n\n",
    "ocr_area": "\n",
    "ocr_par": "\n",
    "ocr_line": " "
}


class HOCRParser:
    def __init__(self, source, is_path=False):
        if not is_path:
            html = BeautifulSoup(source, "html.parser")
        else:
            with open(source, encoding="utf-8") as f:
                data = f.read()
            html = BeautifulSoup(data, "html.parser")

        self.html = html
        self.root = HOCRNode(html.body)

    @property
    def ocr_text(self):
        return self.root.ocr_text


class HOCRNode:
    def __init__(self, html, parent=None):
        self._html = html
        self._parent = parent
        self._children = []
        self._id = None
        self._ocr_class = None
        self._properties = []
        self._coordinates = (0, 0, 0, 0)
        self._confidence = None

        self._parse()

    def _parse(self):
        self._id = self._html.attrs.get("id", None)
        self._ocr_class = self._html.attrs.get("class", [""])[0]
        self._parse_properties()

        for node in self._html.contents:
            self._create_child_node(node)

    def _parse_properties(self):
        title = self._html.attrs.get("title")
        if title:
            self._properties = [x.strip() for x in title.split(";")]

        for property_string in self._properties:
            self._parse_coordinates(property_string)
            self._parse_confidence(property_string)

    def _parse_coordinates(self, string):
        match = COORDINATES_PATTERN.search(string)
        if match:
            self._coordinates = (
                int(float(match.group(1))),
                int(float(match.group(2))),
                int(float(match.group(3))),
                int(float(match.group(4)))
            )

    def _parse_confidence(self, string):
        splt = string.split()

        if not len(splt) > 1:
            return

        if not splt[0].lower() in ["nlp", "x_confs", "x_wconf"]:
            return

        confidences = []
        for val in splt[1:]:
            if not val.isdigit():
                return
            val = int(float(val))
            confidences.append(val)

        self._confidence = sum(confidences) / len(confidences)

    def _create_child_node(self, node):
        if isinstance(node, NavigableString):
            return
        if not node.has_attr("id"):
            return

        child_node = HOCRNode(node, parent=self)
        self._children.append(child_node)

    @property
    def ocr_text(self):
        if len(self._children) == 0:
            return self._html.get_text(strip=True)

        joiner = CHILD_STRING_SEPARATORS.get(self.ocr_class, "\n")

        output = [child.ocr_text for child in self._children]
        output = joiner.join(output)
        return output

    @property
    def html(self):
        """BeautifulSoup-parsed HTML of this element."""
        return self._html

    @property
    def parent(self):
        return self._parent

    @property
    def children(self):
        return self._children

    @property
    def id(self):
        return self._id

    @property
    def ocr_class(self):
        return self._ocr_class

    @property
    def properties(self):
        return self._properties

    @property
    def coordinates(self):
        return self._coordinates

    @property
    def confidence(self):
        return self._confidence


# compatibility layer
from .past import *
