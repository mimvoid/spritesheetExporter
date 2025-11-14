"""
Connects everything in the Spritesheet Exporter plugin to be accessed through Krita.
"""

from krita import Krita, Extension
from builtins import Scripter

from .controller import Controller


class SpritesheetExporter(Extension):
    controller = Controller()

    def __init__(self, parent):
        """
        Always initialise the superclass.
        This is necessary to create the underlying C++ object
        """
        super().__init__(parent)

    def setup(self):
        """Implements the abstract method of Extension.setup()"""
        pass

    def createActions(self, window):
        """
        Adds a menu item to export a spritesheet.
        """

        # parameter 1 = the name Krita uses to identify the action
        # parameter 2 = this script's menu entry name
        # parameter 3 = location of menu entry
        export_action = window.createAction(
            "pykrita_spritesheetExporter", "Export as Spritesheet", "tools/scripts"
        )

        export_action.setToolTip("Export animation in timeline as spritesheet")
        export_action.triggered.connect(self.controller.show_dialog)


Scripter.addExtension(SpritesheetExporter(Krita.instance()))
