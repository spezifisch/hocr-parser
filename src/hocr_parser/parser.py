__author__ = 'Rafa Haro <rh@athento.com>'

from abc import ABCMeta, abstractmethod
from bs4 import BeautifulSoup
import re


class HOCRElement:
    __metaclass__ = ABCMeta

    COORDINATES_PATTERN = re.compile(
        r"bbox\s(-?[0-9.]+)\s(-?[0-9.]+)\s(-?[0-9.]+)\s(-?[0-9.]+)"
    )
    HTML_TAG = None
    HTML_CLASS = None

    def __init__(self, hocr_html, parent=None):
        self._hocr_html = hocr_html
        self._parent = parent
        self.__coordinates = (0, 0, 0, 0)
        self._id = None
        self._elements = []

        self._parse()

    def __hash__(self):
        return hash(self._id)

    def __eq__(self, other):
        if not isinstance(other, HOCRElement):
            return False
        else:
            return self._id == other._id

    def _parse(self):
        self._id = self._hocr_html.attrs.get("id", None)
        title = self._hocr_html.attrs.get("title", "")
        match = HOCRElement.COORDINATES_PATTERN.search(title)
        if match:
            self.__coordinates = (int(match.group(1).split(".")[0]),
                                  int(match.group(2).split(".")[0]),
                                  int(match.group(3).split(".")[0]),
                                  int(match.group(4).split(".")[0]))

        if self._child_node_class:
            tag = self._child_node_class.HTML_TAG
            html_class = self._child_node_class.HTML_CLASS
            children = self._hocr_html.find_all(tag, {"class": html_class})
            for html_child in children:
                hocr_child = self._child_node_class(html_child, parent=self)
                self._elements.append(hocr_child)

    @property
    @abstractmethod
    def _child_node_class(self):
        raise NotImplementedError()

    @property
    def html(self):
        return self._hocr_html.prettify()

    @property
    def parent(self):
        return self._parent

    @property
    def coordinates(self):
        return self.__coordinates

    @property
    def id(self):
        return self._id

    @property
    @abstractmethod
    def ocr_text(self):
        raise NotImplementedError()


class HOCRDocument(HOCRElement):
    def __init__(self, source, is_path=False):
        if not is_path:
            hocr_html = BeautifulSoup(source, "html.parser")
        else:
            hocr_html = BeautifulSoup(open(source, "r").read(), "html.parser")

        super(HOCRDocument, self).__init__(hocr_html, parent=None)

    @property
    def _child_node_class(self):
        return Page

    @property
    def ocr_text(self):
        output = [child.ocr_text for child in self._elements]
        output = "\n\n".join(output)
        return output

    @property
    def pages(self):
        return self._elements

    @property
    def npages(self):
        return len(self._elements)


class Page(HOCRElement):
    HTML_TAG = "div"
    HTML_CLASS = "ocr_page"

    def __init__(self, hocr_html, parent=None):
        super(Page, self).__init__(hocr_html, parent)

    @property
    def _child_node_class(self):
        return Area

    @property
    def ocr_text(self):
        output = [child.ocr_text for child in self._elements]
        output = "\n\n".join(output)
        return output

    @property
    def areas(self):
        return self._elements

    @property
    def nareas(self):
        return len(self._elements)


class Area(HOCRElement):
    HTML_TAG = "div"
    HTML_CLASS = "ocr_carea"

    def __init__(self, hocr_html, parent=None):
        super(Area, self).__init__(hocr_html, parent)

    @property
    def _child_node_class(self):
        return Paragraph

    @property
    def ocr_text(self):
        output = [child.ocr_text for child in self._elements]
        output = "\n".join(output)
        return output

    @property
    def paragraphs(self):
        return self._elements

    @property
    def nparagraphs(self):
        return len(self._elements)


class Paragraph(HOCRElement):
    HTML_TAG = "p"
    HTML_CLASS = "ocr_par"

    def __init__(self, hocr_html, parent=None):
        super(Paragraph, self).__init__(hocr_html, parent)

    @property
    def _child_node_class(self):
        return Line

    @property
    def ocr_text(self):
        output = [child.ocr_text for child in self._elements]
        output = "\n".join(output)
        return output

    @property
    def lines(self):
        return self._elements

    @property
    def nlines(self):
        return len(self._elements)


class Line(HOCRElement):
    HTML_TAG = "span"
    HTML_CLASS = "ocr_line"

    def __init__(self, hocr_html, parent=None):
        super(Line, self).__init__(hocr_html, parent)

    @property
    def _child_node_class(self):
        return Word

    @property
    def ocr_text(self):
        output = [child.ocr_text for child in self._elements]
        output = " ".join(output)
        return output

    @property
    def words(self):
        return self._elements

    @property
    def nwords(self):
        return len(self._elements)


class Word(HOCRElement):
    HTML_TAG = "span"
    HTML_CLASS = "ocrx_word"

    def __init__(self, hocr_html, parent=None):
        super(Word, self).__init__(hocr_html, parent)

    @property
    def _child_node_class(self):
        return None

    @property
    def ocr_text(self):
        text = self._hocr_html.string
        if text:
            return text
        else:
            return ""
