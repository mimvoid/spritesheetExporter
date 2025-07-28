"""
The UI that connects the backend to the frontend with a dialog window
and displays the configuration options to the user.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QGridLayout,
    QVBoxLayout,
    QGroupBox,
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
    QRadioButton,
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
    widget: QWidget
    label: QLabel

    def __init__(self, widget: QWidget, description: str, tooltip: str | None = None):
        self.widget = widget

        self.label = QLabel(description)
        self.label.setBuddy(widget)

        if tooltip:
            widget.setToolTip(tooltip)
            self.label.setToolTip(tooltip)


class DirectionRadio(QHBoxLayout):
    h_dir = QRadioButton(text="Horizontal")
    v_dir = QRadioButton(text="Vertical")

    def __init__(self):
        super().__init__()

        self.h_dir.setChecked(True)

        self.addWidget(QLabel("Sprite placement direction:"))
        self.addWidget(self.h_dir)
        self.addWidget(self.v_dir)


class UISpritesheetExporter:
    exp = SpritesheetExporter()

    # the main window
    main_dialog = QDialog()

    # the box holding everything
    outer_layout = QVBoxLayout(main_dialog)
    top_layout = QVBoxLayout()

    # the user should choose the export name of the final spritesheet
    export_name = QLineEdit()

    advanced_settings = QGroupBox("Advanced Settings")
    advanced_layout = QVBoxLayout()

    # we let people export each layer as an animation frame if they wish
    layers_as_animation = QCheckBox(text="Use layers as animation frames")
    write_texture_atlas = QCheckBox(text="Write JSON texture atlas")

    # We want to let the user choose if they want the final spritesheet
    # to be horizontally- or vertically-oriented.
    direction = DirectionRadio()

    force_new = QCheckBox(text="Force new folder")

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

        self.advanced_settings.setCheckable(True)
        self.advanced_settings.setChecked(False)

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

        self.action_button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.action_button_box.accepted.connect(self.confirmButton)
        self.action_button_box.rejected.connect(self.main_dialog.close)

        self.exportPath = Path.home()

        self.initialize_export()

    # I would have used QFormLayout's addRow
    # except it doesn't let you add a tooltip to the row's name
    # (adding a tooltip to the whole layout would have been best
    #  but doesn't seem possible)
    def add_described_widget(self, parent, listWidgets, align=Qt.AlignLeft):
        layout = QGridLayout()

        for row, widget in enumerate(listWidgets):
            layout.addWidget(widget.label, row, 0)
            layout.addWidget(widget.widget, row, 1)

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
                    self.export_name,
                    "Export name:",
                    "The name of the exported spritesheet file",
                )
            ],
        )
        self.add_described_widget(
            parent=self.top_layout,
            listWidgets=[
                DescribedWidget(
                    self.export_dir_tx,
                    "Export directory:",
                    "The directory the spritesheet will be exported to",
                )
            ],
        )

        self.export_dir.addWidget(self.export_dir_butt)
        self.export_dir.addWidget(self.export_dir_reset_butt)

        self.top_layout.addLayout(self.export_dir)
        self.top_layout.addWidget(self.write_texture_atlas)

        self.outer_layout.addLayout(self.top_layout, 0)

        # Hidden under Advanced Settings
        self.advanced_layout.addWidget(self.layers_as_animation)
        self.advanced_layout.addItem(QSpacerItem(10, 10))
        self.advanced_layout.addLayout(self.direction)
        self.advanced_layout.addItem(QSpacerItem(20, 20))

        defaultsHint = QLabel("Leave any parameter at 0 to get a default value:")
        defaultsHint.setToolTip(
            "For example with 16 sprites, leaving both rows and columns at 0\n"
            + "will set their defaults to 4 each\n"
            + "while leaving only columns at 0 and rows at 1\n"
            + "will set columns default at 16"
        )
        self.advanced_layout.addWidget(defaultsHint)

        self.add_described_widget(
            parent=self.spin_boxes,
            listWidgets=[
                DescribedWidget(
                    self.rows,
                    "Rows:",
                    "Number of rows of the spritesheet;\n"
                    + "default is assigned depending on columns number\n"
                    + "or if 0 columns tries to form a square ",
                ),
                DescribedWidget(
                    self.columns,
                    "Columns:",
                    "Number of columns of the spritesheet;\n"
                    + "default is assigned depending on rows number\n"
                    + "or if 0 rows tries to form a square",
                ),
            ],
        )

        self.add_described_widget(
            parent=self.spin_boxes,
            listWidgets=[
                DescribedWidget(
                    self.start,
                    "Start:",
                    "First frame of the animation timeline (included) "
                    + "to be added to the spritesheet;\n"
                    + "default is first keyframe after "
                    + "the Start frame of the Animation docker",
                ),
                DescribedWidget(
                    self.end,
                    "End:",
                    "Last frame of the animation timeline (included) "
                    + "to be added to the spritesheet;\n"
                    + "default is last keyframe before "
                    + "the End frame of the Animation docker",
                ),
                DescribedWidget(
                    self.step,
                    "Step:",
                    "only consider every 'step' frame "
                    + "to be added to the spritesheet;\n"
                    + "default is 1 (use every frame)",
                ),
            ],
        )

        self.advanced_layout.addWidget(self.spin_boxes_widget)

        # self.force_new.setTooltip(
        #     "If there is already a folder with the same name as the individual sprites export folder,\n"
        #     + "whether to create a new one (checked) or write the sprites in the existing folder,\n"
        #     + "possibly overwriting other files (unchecked)",
        # )
        self.advanced_layout.addWidget(self.force_new)

        self.advanced_settings.setLayout(self.advanced_layout)
        self.outer_layout.addWidget(self.advanced_settings)

        self.outer_layout.addWidget(self.action_button_box)

    def exclusiveVertToHor(self):
        self.exclusiveCheckBoxUpdate(trigger=self.v_dir, triggered=self.h_dir)

    def exclusiveHorToVert(self):
        self.exclusiveCheckBoxUpdate(trigger=self.h_dir, triggered=self.v_dir)

    def exclusiveCheckBoxUpdate(self, trigger, triggered):
        if triggered.isChecked() == trigger.isChecked():
            triggered.setChecked(not trigger.isChecked())

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
        self.exp.force_new = self.force_new.isChecked()
        self.exp.export()
        self.main_dialog.hide()
