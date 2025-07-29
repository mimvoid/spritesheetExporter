"""
The UI that connects the backend to the frontend with a dialog window
and displays the configuration options to the user.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFormLayout,
    QGroupBox,
    QFrame,
    QPushButton,
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
from typing import Optional
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


class CommonSettings(QFormLayout):
    name = QLineEdit()
    directory = QLineEdit()
    change_dir = QPushButton(KI.icon("folder"), None)
    reset_dir = QPushButton(KI.icon("view-refresh"), None)

    export_frames = QCheckBox("Export individual frames")
    write_texture_atlas = QCheckBox("Write JSON texture atlas")

    def __init__(self):
        super().__init__()

        self.name.setToolTip("The name of the exported spritesheet file")
        self.directory.setToolTip("The directory the spritesheet will be exported to")

        self.change_dir.setToolTip("Open a file picker to choose the export directory")
        self.reset_dir.setToolTip(
            "Reset export directory to the current document's directory"
        )

        self.export_frames.setToolTip("Export each sprite frame into its own file")
        self.write_texture_atlas.setToolTip(
            "Write a JSON texture atlas that can be used in game frameworks (e.g. Phaser 3)"
        )

        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self.directory)
        dir_layout.addWidget(self.change_dir)
        dir_layout.addWidget(self.reset_dir)

        self.addRow("Export name:", self.name)
        self.addRow("Export directory:", dir_layout)
        self.addRow(self.export_frames)
        self.addRow(self.write_texture_atlas)

    def apply_settings(self, exp: SpritesheetExporter):
        exp.export_name = self.name.text().split(".")[0]
        exp.export_dir = Path(self.directory.text())
        exp.export_individual_frames = self.export_frames.isChecked()
        exp.write_texture_atlas = self.write_texture_atlas.isChecked()


class DirectionRadio(QHBoxLayout):
    """
    Lets the user choose if they want the final spreadsheet to be
    horizontally or vertically oriented.
    """

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

    dialog = QDialog()  # the main window
    root_layout = QVBoxLayout(dialog)  # the box holding everything

    common_settings = CommonSettings()

    # Advanced settings group
    advanced_settings = QGroupBox("Advanced Settings")
    advanced_layout = QVBoxLayout()

    layers_as_animation = QCheckBox(text="Use layers as animation frames")
    direction = DirectionRadio()

    # a box holding the boxes with rows columns and start end
    spin_boxes_widget = QFrame()
    spin_boxes = QHBoxLayout(spin_boxes_widget)

    rows = QSpinBox(minimum=DEFAULT_SPACE)
    columns = QSpinBox(minimum=DEFAULT_SPACE)

    start = QSpinBox(minimum=DEFAULT_TIME, maximum=9999)
    end = QSpinBox(minimum=DEFAULT_TIME, maximum=9999)
    step = QSpinBox(minimum=1)

    force_new = QCheckBox(text="Force new folder")

    dialog_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

    def __init__(self):
        # the window is not modal and does not block input to other windows
        self.dialog.setWindowModality(Qt.NonModal)
        self.dialog.setMinimumSize(500, 100)

        self.common_settings.name.setText(self.exp.export_name)
        self.common_settings.change_dir.clicked.connect(self.change_export_dir)
        self.common_settings.reset_dir.clicked.connect(self.reset_export_dir)

        self.advanced_settings.setCheckable(True)
        self.advanced_settings.setChecked(False)
        self.advanced_settings.setLayout(self.advanced_layout)

        self.spin_boxes_widget.setFrameShape(QFrame.Panel)
        self.spin_boxes_widget.setFrameShadow(QFrame.Sunken)

        self.rows.setValue(DEFAULT_SPACE)
        self.columns.setValue(DEFAULT_SPACE)

        self.start.setValue(DEFAULT_TIME)
        self.end.setValue(DEFAULT_TIME)
        self.step.setValue(1)

        self.dialog_buttons.accepted.connect(self.confirmButton)
        self.dialog_buttons.rejected.connect(self.dialog.close)

        self.initialize_export()

    # I would have used QFormLayout's addRow
    # except it doesn't let you add a tooltip to the row's name
    # (adding a tooltip to the whole layout would have been best
    #  but doesn't seem possible)
    @staticmethod
    def add_described_widget(parent, listWidgets, align=Qt.AlignLeft):
        layout = QGridLayout()

        for row, widget in enumerate(listWidgets):
            layout.addWidget(widget.label, row, 0)
            layout.addWidget(widget.widget, row, 1)

        layout.setAlignment(align)
        parent.addLayout(layout)
        return layout

    def initialize_export(self):
        self.root_layout.addLayout(self.common_settings)

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

        self.force_new.setToolTip(
            "If there is already a folder with the same name as the individual sprites export folder,\n"
            + "whether to create a new one (checked) or write the sprites in the existing folder,\n"
            + "possibly overwriting other files (unchecked)",
        )
        self.advanced_layout.addWidget(self.force_new)

        self.root_layout.addWidget(self.advanced_settings)
        self.root_layout.addWidget(self.dialog_buttons)

    def show_dialog(self):
        if self.common_settings.directory.text() == "":
            self.reset_export_dir()

        self.dialog.setWindowTitle(i18n("SpritesheetExporter"))
        self.dialog.setSizeGripEnabled(True)
        self.dialog.show()
        self.dialog.activateWindow()
        self.dialog.setDisabled(False)

    @staticmethod
    def current_directory() -> Optional[Path]:
        doc = KI.activeDocument()
        if not doc or not doc.fileName():
            return None
        return Path(doc.fileName()).parent

    def change_export_dir(self):
        file_dialog = QFileDialog()
        file_dialog.setWindowTitle(i18n("Choose Export Directory"))
        file_dialog.setSizeGripEnabled(True)

        # QFileDialog already seems to handle invalid directories fine
        file_dialog.setDirectory(self.common_settings.directory.text())

        # we grab the output path on directory changed
        path = file_dialog.getExistingDirectory()
        if path != "":
            self.common_settings.directory.setText(str(path))

    def reset_export_dir(self):
        path = UISpritesheetExporter.current_directory()
        if path:
            self.common_settings.directory.setText(str(path))

    def confirmButton(self):
        # if you double click it shouldn't interrupt
        # the first run of the function with a new one
        self.dialog.setDisabled(True)

        self.common_settings.apply_settings(self.exp)

        self.exp.layers_as_animation = self.layers_as_animation.isChecked()
        self.exp.horizontal = self.direction.h_dir.isChecked()
        self.exp.rows = self.rows.value()
        self.exp.columns = self.columns.value()
        self.exp.start = self.start.value()
        self.exp.end = self.end.value()
        self.exp.step = self.step.value()
        self.exp.force_new = self.force_new.isChecked()

        self.exp.export()
        self.dialog.hide()
