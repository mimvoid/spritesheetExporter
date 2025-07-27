"""
spritesheet exporter from animation timeline
(all visible layers)

"""

from krita import Extension, Krita
from builtins import Scripter

from .se_ui import UISpritesheetExporter
# manages the dialog that lets you
# set user preferences before applying the script


class SpritesheetExporterExtension(Extension):
    ui = UISpritesheetExporter()

    # Always initialise the superclass.
    # This is necessary to create the underlying C++ object
    def __init__(self, parent):
        super().__init__(parent)

    # this too is necessary, because "Extension.setup() is abstract
    # and must be overridden" and we inherit from Extension
    def setup(self):
        pass

    # menu stuff
    # don't forget to activate the script in krita's preferences
    # or it won't show
    def createActions(self, window):
        # parameter 1 = the name that Krita uses to identify the action
        # parameter 2 = this script's menu entry name
        # parameter 3 = location of menu entry
        exportAction = window.createAction(
            "pykrita_spritesheetExporter", "Export as Spritesheet", "tools/scripts"
        )

        exportAction.setToolTip("Export animation in timeline as spritesheet")
        # doesn't show tooltip on mouse hover. Why?

        # when you click on the script in the menu it opens the dialog window
        exportAction.triggered.connect(self.ui.showExportDialog)


# the backend is in spritesheet_exporter.py

app = Krita.instance()
Scripter.addExtension(SpritesheetExporterExtension(app))
