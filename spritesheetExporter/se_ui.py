"""
The UI that connects the backend to the frontend with a dialog window
and displays the configuration options to the user.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QFrame,
    QPushButton,
    QFileDialog,
    QSpinBox,
    QDialog,
    QLineEdit,
    QCheckBox,
    QDialogButtonBox,
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


class DirectionRadio(QFormLayout):
    """
    Lets the user choose if they want the final spreadsheet to be
    horizontally or vertically oriented.
    """

    h_dir = QRadioButton("Horizontal")
    v_dir = QRadioButton("Vertical")

    def __init__(self):
        super().__init__()

        self.h_dir.setChecked(True)

        buttons = QHBoxLayout()
        buttons.addWidget(self.h_dir)
        buttons.addWidget(self.v_dir)
        self.addRow("Sprite placement direction:", buttons)


class SpinBoxes(QFrame):
    rows = QSpinBox(minimum=DEFAULT_SPACE)
    columns = QSpinBox(minimum=DEFAULT_SPACE)

    start = QSpinBox(minimum=DEFAULT_TIME, maximum=9999)
    end = QSpinBox(minimum=DEFAULT_TIME, maximum=9999)
    step = QSpinBox(minimum=1)

    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.Panel)
        self.setFrameShadow(QFrame.Sunken)

        self.rows.setValue(DEFAULT_SPACE)
        self.columns.setValue(DEFAULT_SPACE)

        self.rows.setToolTip(
            "If left 0, number of rows depends on columns.\nIf both are 0, tries to form a square"
        )
        self.columns.setToolTip(
            "If left 0, number of columns depends rows.\nIf both are 0, tries to form a square"
        )

        self.start.setValue(DEFAULT_TIME)
        self.end.setValue(DEFAULT_TIME)
        self.step.setValue(1)

        self.start.setToolTip("First frame time of the animation (inclusive)")
        self.end.setToolTip("Last frame time of the animation (inclusive)")
        self.step.setToolTip(
            "Only export each 'step' number of frames.\nDefaults to every frame"
        )

        space = QFormLayout()
        space.addRow("Rows:", self.rows)
        space.addRow("Columns:", self.columns)

        time = QFormLayout()
        time.addRow("Start:", self.start)
        time.addRow("End:", self.end)
        time.addRow("Step:", self.step)

        layout = QHBoxLayout(self)
        layout.addLayout(space)
        layout.addLayout(time)

    def apply_settings(self, exp: SpritesheetExporter):
        exp.rows = self.rows.value()
        exp.columns = self.columns.value()
        exp.start = self.start.value()
        exp.end = self.end.value()
        exp.step = self.step.value()


class UISpritesheetExporter:
    exp = SpritesheetExporter()
    dialog = QDialog()  # the main window

    common_settings = CommonSettings()

    # Extra settings group
    layers_as_animation = QCheckBox("Use layers as animation frames")
    direction = DirectionRadio()
    spin_boxes = SpinBoxes()
    force_new = QCheckBox("Force new folder")

    dialog_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

    def __init__(self):
        # the window is not modal and does not block input to other windows
        self.dialog.setWindowModality(Qt.NonModal)
        self.dialog.setMinimumSize(500, 100)

        self.common_settings.name.setText(self.exp.export_name)
        self.common_settings.change_dir.clicked.connect(self.change_export_dir)
        self.common_settings.reset_dir.clicked.connect(self.reset_export_dir)

        self.layers_as_animation.setToolTip(
            "Whether to export each individual frame into its own file"
        )
        self.force_new.setToolTip(
            "If checked, create a new individual frames folder if one already exists.\nOtherwise, write the sprites in the existing folder (may overwrite files)"
        )

        self.dialog_buttons.accepted.connect(self.confirmButton)
        self.dialog_buttons.rejected.connect(self.dialog.close)

        # Setup layouts
        extra_settings = QGroupBox("Extra Settings")
        extra_settings.setCheckable(True)
        extra_settings.setChecked(False)

        extras = QVBoxLayout()
        extra_settings.setLayout(extras)

        extras.addWidget(self.layers_as_animation)
        extras.addSpacing(10)
        extras.addLayout(self.direction)
        extras.addSpacing(20)
        extras.addWidget(self.spin_boxes)
        extras.addWidget(self.force_new)

        root_layout = QVBoxLayout(self.dialog)  # the box holding everything
        root_layout.addLayout(self.common_settings)
        root_layout.addWidget(extra_settings)
        root_layout.addWidget(self.dialog_buttons)

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

        self.spin_boxes.apply_settings(self.exp)

        self.exp.force_new = self.force_new.isChecked()

        self.exp.export()
        self.dialog.hide()
