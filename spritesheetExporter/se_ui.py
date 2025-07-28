"""
UI of the spritesheet exporter user choices dialog

"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QGridLayout,
    QVBoxLayout,
    QFrame,
    QPushButton,
    QHBoxLayout,
    QFileDialog,
    QLabel,
    QSpinBox,
    QDialog,
    QLineEdit,
    QWidget,
    QCheckBox,
    QDialogButtonBox,
    QSpacerItem,
)
from builtins import i18n

# we want paths to work whether it's windows or unix
from pathlib import Path
from .spritesheet_exporter import (
    SpritesheetExporter,
    KI,
    DEFAULT_SPACE,
    DEFAULT_TIME,
)


class DescribedWidget:
    def __init__(self, widget, descri, tooltip=""):
        self.widget = widget
        self.descri = descri
        self.tooltip = tooltip


class UISpritesheetExporter:
    exp = SpritesheetExporter()

    # the main window
    main_dialog = QDialog()

    # the box holding everything
    outer_layout = QVBoxLayout(main_dialog)
    top_layout = QVBoxLayout()

    # the user should choose the export name of the final spritesheet
    export_name = QLineEdit()

    def __init__(self):
        # the window is not modal and does not block input to other windows
        self.main_dialog.setWindowModality(Qt.NonModal)
        self.main_dialog.setMinimumSize(500, 100)

        # and the export directory
        self.export_dir_tx = QLineEdit()
        self.export_dir_butt = QPushButton("Change export directory")
        self.export_dir_reset_butt = QPushButton("Reset to current directory")
        self.export_dir_reset_butt.setToolTip(
            "Reset export directory to current .kra document's directory"
        )
        self.export_dir_butt.clicked.connect(self.changeExportDir)
        self.export_dir_reset_butt.clicked.connect(self.resetExportDir)
        self.export_dir = QHBoxLayout()

        self.custom_settings = QCheckBox()
        self.custom_settings.setChecked(False)
        self.custom_settings.stateChanged.connect(self.toggleHideable)

        self.hideable_widget = QFrame()  # QFrames are a type of widget
        self.hideable_widget.setFrameShape(QFrame.Panel)
        self.hideable_widget.setFrameShadow(QFrame.Sunken)
        self.hideable_layout = QVBoxLayout(self.hideable_widget)

        # we let people export each layer as an animation frame if they wish
        self.layers_as_animation = QCheckBox()
        self.layers_as_animation.setChecked(False)

        self.write_texture_atlas = QCheckBox()
        self.write_texture_atlas.setChecked(False)

        # We want to let the user choose if they want the final spritesheet
        # to be horizontally- or vertically-oriented.
        # There is a nifty thing called QButtonGroup() but
        # it doesn't seem to let you add names between each checkbox somehow?
        self.h_dir = QCheckBox()
        self.h_dir.setChecked(True)
        self.v_dir = QCheckBox()
        self.v_dir.setChecked(False)
        self.v_dir.stateChanged.connect(self.exclusiveVertToHor)
        self.h_dir.stateChanged.connect(self.exclusiveHorToVert)
        self.direction = QHBoxLayout()

        self.spin_boxes_widget = QFrame()
        self.spin_boxes_widget.setFrameShape(QFrame.Panel)
        self.spin_boxes_widget.setFrameShadow(QFrame.Sunken)

        # a box holding the boxes with rows columns and start end
        self.spin_boxes = QHBoxLayout(self.spin_boxes_widget)

        self.rows = QSpinBox(minimum=DEFAULT_SPACE)
        self.columns = QSpinBox(minimum=DEFAULT_SPACE)
        self.rows.setValue(DEFAULT_SPACE)
        self.columns.setValue(DEFAULT_SPACE)

        self.start = QSpinBox(minimum=DEFAULT_TIME, maximum=9999)
        self.end = QSpinBox(minimum=DEFAULT_TIME, maximum=9999)
        self.step = QSpinBox(minimum=1)
        self.start.setValue(DEFAULT_TIME)
        self.end.setValue(DEFAULT_TIME)
        self.step.setValue(1)

        # to be placed outside of spinBoxes, still in outerLayout
        self.hiddenCheckbox = QWidget()
        self.hiddenCheckboxLayout = QVBoxLayout(self.hiddenCheckbox)
        self.line = QFrame()
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)
        self.checkBoxes = QHBoxLayout()
        self.forceNew = QCheckBox()
        self.forceNew.setChecked(False)
        self.removeTmp = QCheckBox()
        self.removeTmp.setChecked(True)

        self.line2 = QFrame()
        self.line2.setFrameShape(QFrame.HLine)
        self.line2.setFrameShadow(QFrame.Sunken)
        self.action_button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.action_button_box.accepted.connect(self.confirmButton)
        self.action_button_box.rejected.connect(self.main_dialog.close)

        self.space = 10

        self.spacer = QSpacerItem(self.space, self.space)
        self.spacerBig = QSpacerItem(self.space * 2, self.space * 2)

        self.exportPath = Path.home()

        self.initialize_export()

    # I would have used QFormLayout's addRow
    # except it doesn't let you add a tooltip to the row's name
    # (adding a tooltip to the whole layout would have been best
    #  but doesn't seem possible)
    def add_described_widget(self, parent, listWidgets, align=Qt.AlignLeft):
        layout = QGridLayout()
        row = 0
        for widget in listWidgets:
            label = QLabel(widget.descri)
            label.setBuddy(widget.widget)
            layout.addWidget(label, row, 0)
            layout.addWidget(widget.widget, row, 1)
            if widget.tooltip != "":
                widget.widget.setToolTip(widget.tooltip)
                label.setToolTip(widget.tooltip)
            row += 1
        layout.setAlignment(align)
        parent.addLayout(layout)
        return layout

    def initialize_export(self):
        # putting stuff in boxes
        # and boxes in bigger boxes
        self.export_name.setText(self.exp.export_name)
        self.add_described_widget(
            parent=self.top_layout,
            listWidgets=[
                DescribedWidget(
                    widget=self.export_name,
                    descri="Export name:",
                    tooltip="The name of the exported spritesheet file",
                )
            ],
        )
        self.add_described_widget(
            parent=self.top_layout,
            listWidgets=[
                DescribedWidget(
                    widget=self.export_dir_tx,
                    descri="Export Directory:",
                    tooltip="The directory the spritesheet will be exported to",
                )
            ],
        )

        self.export_dir.addWidget(self.export_dir_butt)
        self.export_dir.addWidget(self.export_dir_reset_butt)
        self.top_layout.addLayout(self.export_dir)

        self.add_described_widget(
            parent=self.top_layout,
            listWidgets=[
                DescribedWidget(
                    descri="Write json texture atlas ",
                    widget=self.write_texture_atlas,
                    tooltip=""
                    + "Write a json texture atlas that can be\n"
                    + "used in e.g. the Phaser 3 game framework",
                )
            ],
        )

        self.add_described_widget(
            parent=self.top_layout,
            listWidgets=[
                DescribedWidget(
                    widget=self.custom_settings,
                    descri="Use Custom export Settings:",
                    tooltip=""
                    + "Whether to set yourself the number of rows, columns,\n"
                    + "first and last frame, etc. (checked)\n"
                    + "or use the default values (unchecked) ",
                )
            ],
        )

        self.outer_layout.addLayout(self.top_layout, 0)

        # all this stuff will be hideable
        self.add_described_widget(
            parent=self.hideable_layout,
            listWidgets=[
                DescribedWidget(
                    descri="use layers as animation frames ",
                    widget=self.layers_as_animation,
                    tooltip="Rather than exporting a spritesheet "
                    + "using as frames\n"
                    + "each frame of the timeline "
                    + "(all visible layers merged down),\n"
                    + "export instead a spritesheet "
                    + "using as frames\n"
                    + "the current frame of each visible layer",
                )
            ],
        )

        self.hideable_layout.addItem(self.spacer)

        self.direction.addWidget(QLabel("sprites placement direction: \t"))
        self.add_described_widget(
            parent=self.direction,
            listWidgets=[
                DescribedWidget(
                    widget=self.h_dir,
                    descri="Horizontal:",
                    tooltip="like so:\n1, 2, 3\n4, 5, 6\n7, 8, 9",
                )
            ],
        )

        self.add_described_widget(
            parent=self.direction,
            listWidgets=[
                DescribedWidget(
                    widget=self.v_dir,
                    descri="Vertical:",
                    tooltip="like so:\n1, 4, 7\n2, 5, 8\n3, 6, 9",
                )
            ],
        )

        self.hideable_layout.addLayout(self.direction)

        self.hideable_layout.addItem(self.spacerBig)

        defaultsHint = QLabel("Leave any parameter at 0 to get a default value:")
        defaultsHint.setToolTip(
            "For example with 16 sprites, "
            + "leaving both rows and columns at 0\n"
            + "will set their defaults to 4 each\n"
            + "while leaving only columns at 0 and rows at 1\n"
            + "will set columns default at 16"
        )
        self.hideable_layout.addWidget(defaultsHint)

        self.add_described_widget(
            parent=self.spin_boxes,
            listWidgets=[
                DescribedWidget(
                    widget=self.rows,
                    descri="Rows:",
                    tooltip="Number of rows of the spritesheet;\n"
                    + "default is assigned depending on columns number\n"
                    + "or if 0 columns tries to form a square ",
                ),
                DescribedWidget(
                    widget=self.columns,
                    descri="Columns:",
                    tooltip="Number of columns of the spritesheet;\n"
                    + "default is assigned depending on rows number\n"
                    + "or if 0 rows tries to form a square",
                ),
            ],
        )

        self.add_described_widget(
            parent=self.spin_boxes,
            listWidgets=[
                DescribedWidget(
                    widget=self.start,
                    descri="Start:",
                    tooltip=""
                    + "First frame of the animation timeline (included) "
                    + "to be added to the spritesheet;\n"
                    + "default is first keyframe after "
                    + "the Start frame of the Animation docker",
                ),
                DescribedWidget(
                    widget=self.end,
                    descri="End:",
                    tooltip="Last frame of the animation timeline (included) "
                    + "to be added to the spritesheet;\n"
                    + "default is last keyframe before "
                    + "the End frame of the Animation docker",
                ),
                DescribedWidget(
                    widget=self.step,
                    descri="Step:",
                    tooltip="only consider every 'step' frame "
                    + "to be added to the spritesheet;\n"
                    + "default is 1 (use every frame)",
                ),
            ],
        )

        self.hideable_layout.addWidget(self.spin_boxes_widget)

        self.add_described_widget(
            parent=self.checkBoxes,
            listWidgets=[
                DescribedWidget(
                    descri="Remove individual sprites?",
                    widget=self.removeTmp,
                    tooltip="Once the spritesheet export is done,\n"
                    + "whether to remove the individual exported sprites",
                )
            ],
        )

        self.forceNewLayout = self.add_described_widget(
            parent=self.hiddenCheckboxLayout,
            listWidgets=[
                DescribedWidget(
                    descri="Force new folder?",
                    widget=self.forceNew,
                    tooltip="If there is already a folder "
                    + "with the same name as the individual "
                    + "sprites export folder,\n"
                    + "whether to create a new one (checked) "
                    + "or write the sprites in the existing folder,\n"
                    + "possibly overwriting other files (unchecked)",
                )
            ],
        )

        # have removeTmp toggle forceNew's and sprites export dir's visibility
        self.checkBoxes.addWidget(self.hiddenCheckbox)
        self.hideable_layout.addLayout(self.checkBoxes)
        self.removeTmp.clicked.connect(self.toggleHiddenParams)

        self.outer_layout.addWidget(self.hideable_widget)

        self.outer_layout.addWidget(self.action_button_box)
        self.toggleHiddenParams()
        self.toggleHideable()

    def exclusiveVertToHor(self):
        self.exclusiveCheckBoxUpdate(trigger=self.v_dir, triggered=self.h_dir)

    def exclusiveHorToVert(self):
        self.exclusiveCheckBoxUpdate(trigger=self.h_dir, triggered=self.v_dir)

    def exclusiveCheckBoxUpdate(self, trigger, triggered):
        if triggered.isChecked() == trigger.isChecked():
            triggered.setChecked(not trigger.isChecked())

    def toggleHideable(self):
        if self.custom_settings.isChecked():
            self.hideable_widget.show()
            self.main_dialog.adjustSize()
        else:
            self.hideable_widget.hide()
            self.main_dialog.adjustSize()

    def toggleHiddenParams(self):
        if self.removeTmp.isChecked():
            self.forceNew.setChecked(False)
        self.hiddenCheckbox.setDisabled(self.removeTmp.isChecked())

    def showExportDialog(self):
        self.doc = KI.activeDocument()
        if self.export_dir_tx.text() == "":
            self.resetExportDir()
        self.main_dialog.setWindowTitle(i18n("SpritesheetExporter"))
        self.main_dialog.setSizeGripEnabled(True)
        self.main_dialog.show()
        self.main_dialog.activateWindow()
        self.main_dialog.setDisabled(False)

    def changeExportDir(self):
        self.exportDirDialog = QFileDialog()
        self.exportDirDialog.setWindowTitle(i18n("Choose Export Directory"))
        self.exportDirDialog.setSizeGripEnabled(True)
        self.exportDirDialog.setDirectory(str(self.exportPath))
        # we grab the output path on directory changed
        self.exportPath = self.exportDirDialog.getExistingDirectory()
        if self.exportPath != "":
            self.export_dir_tx.setText(str(self.exportPath))

    # go back to the same folder where your .kra is
    def resetExportDir(self):
        if self.doc and self.doc.fileName():
            self.exportPath = Path(self.doc.fileName()).parents[0]
        self.export_dir_tx.setText(str(self.exportPath))

    def confirmButton(self):
        # if you double click it shouldn't interrupt
        # the first run of the function with a new one
        self.main_dialog.setDisabled(True)

        self.exp.export_name = self.export_name.text().split(".")[0]
        self.exp.export_dir = Path(self.exportPath)
        self.exp.layers_as_animation = self.layers_as_animation.isChecked()
        self.exp.write_texture_atlas = self.write_texture_atlas.isChecked()
        self.exp.horizontal = self.h_dir.isChecked()
        self.exp.rows = self.rows.value()
        self.exp.columns = self.columns.value()
        self.exp.start = self.start.value()
        self.exp.end = self.end.value()
        self.exp.step = self.step.value()
        self.exp.removeTmp = self.removeTmp.isChecked()
        self.exp.force_new = self.forceNew.isChecked()
        self.exp.export()
        self.main_dialog.hide()
