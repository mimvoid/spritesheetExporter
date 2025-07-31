"""
Miscellaneous utilities.
"""

from krita import Node
from builtins import Application


def _recurse_children(node: Node, result: list[Node]) -> list[Node]:
    """
    A simple implementation of Node.findChildNodes() for below version 4.2.0.
    """

    append = result.append  # Local variables can speed up Python execution

    for child in node.childNodes():
        append(child)
        if child.childNodes() != []:
            _recurse_children(child, result)

    return result


def _filter_recurse_children(node: Node, type: str, result: list[Node]) -> list[Node]:
    """
    Similar to _recurse_children, but filters by layer type.
    """

    append = result.append

    for child in node.childNodes():
        if child.type() == type:
            append(child)
        if child.childNodes() != []:
            _filter_recurse_children(child, type, result)

    return result


class KritaVersion:
    can_analyze_time: bool
    can_set_modified: bool
    can_find_child_nodes: bool

    def __init__(self):
        major, minor, patch = [int(i) for i in Application.version().split(".")[0:3]]
        if major > 5:
            self.can_analyze_time = True
            self.can_set_modified = True
            self.can_find_child_nodes = True
        elif major == 5:
            self.can_analyze_time = True
            self.can_set_modified = minor > 1 or (minor == 1 and patch >= 2)
            self.can_find_child_nodes = minor >= 2
        else:
            self.can_analyze_time = major == 4 and minor >= 2
            self.can_set_modified = False
            self.can_find_child_nodes = False

    def recurse_children(self, node: Node, type="") -> list[Node]:
        """
        A simple version of Node.findChildNodes() that works before version 4.2.0.
        Note that the custom pre-4.2.0 implementation is slower.

        @param node The layer of the children to find recursively
        @param type The layer type to filter by. If empty, gets layers of all types.
        See Node.type() for available options.
        """

        if self.can_find_child_nodes:
            return node.findChildNodes("", True)

        if type != "":
            return _filter_recurse_children(node, type, [])

        return _recurse_children(node, [])
