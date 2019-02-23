# compatibility layer for previous hocr_parser versions

from .parser import HOCRNode, HOCRParser
from bs4.element import NavigableString


class HOCRElement(HOCRNode):
    def __init__(self, hocr_html, parent=None, next_tag=None, next_attribute=None, next_class=None):
        super().__init__(hocr_html, parent)

    def __hash__(self):
        return hash(self._id)

    def __eq__(self, other):
        if not isinstance(other, HOCRElement):
            return False
        else:
            return self._id == other._id

    def _create_child_node(self, node):
        # we need to override this method to return HOCRElement instead of HOCRNode

        if isinstance(node, NavigableString):
            return
        if not node.has_attr("id"):
            return

        child_node = HOCRElement(node, parent=self)
        self._children.append(child_node)

    @property
    def _hocr_html(self):
        return self.html

    @property
    def pages(self):
        return self.children

    @property
    def npages(self):
        return len(self.children)

    @property
    def areas(self):
        return self.children

    @property
    def nareas(self):
        return len(self.children)

    @property
    def paragraphs(self):
        return self.children

    @property
    def nparagraphs(self):
        return len(self.children)

    @property
    def lines(self):
        return self.children

    @property
    def nlines(self):
        return len(self.children)

    @property
    def words(self):
        return self.children

    @property
    def nwords(self):
        return len(self.children)


class HOCRDocument(HOCRParser):
    def __init__(self, source, is_path=False):
        super().__init__(source, is_path)
        # we need to return HOCRElement instead of HOCRNode
        self.root = HOCRElement(self.html.body)

    @property
    def pages(self):
        return self.root.children


class Page(HOCRElement):
    pass


class Area(HOCRElement):
    pass


class Paragraph(HOCRElement):
    pass


class Line(HOCRElement):
    pass


class Word(HOCRElement):
    pass
