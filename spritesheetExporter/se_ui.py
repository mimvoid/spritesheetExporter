"""
The UI that connects the backend to the frontend with a dialog window
and displays the configuration options to the user.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGridLayout,
    QGroupBox,
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

from pathlib import Path  # Operating system-independent path operations
from typing import Optional
from .spritesheet_exporter import (
    SpritesheetExporter,
    KI,
    DEFAULT_SPACE,
    DEFAULT_TIME,
)


class CommonSettings(QFormLayout):
    name = QLineEdit("spritesheet.png")
    directory = QLineEdit()
    change_dir = QPushButton(KI.icon("folder"), None)
    reset_dir = QPushButton(KI.icon("view-refresh"), None)

    unique_frames = QCheckBox("Only unique frames")
    write_texture_atlas = QCheckBox("Write JSON texture atlas")

    def __init__(self):
        super().__init__()

        self.name.setToolTip("The name of the exported spritesheet file")
        self.directory.setToolTip("The directory the spritesheet will be exported to")

        self.change_dir.setToolTip("Open a file picker to choose the export directory")
        self.reset_dir.setToolTip(
            "Reset export directory to the current document's directory"
        )

        self.write_texture_atlas.setToolTip(
            "Write a JSON texture atlas that can be used in game frameworks (e.g. Phaser 3)"
        )

        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self.directory)
        dir_layout.addWidget(self.change_dir)
        dir_layout.addWidget(self.reset_dir)

        self.addRow("Export name:", self.name)
        self.addRow("Export directory:", dir_layout)
        self.addRow(self.unique_frames)
        self.addRow(self.write_texture_atlas)

    def apply_settings(self, exp: SpritesheetExporter):
        exp.export_path = Path(self.directory.text(), self.name.text())
        exp.unique_frames = self.unique_frames.isChecked()
        exp.write_texture_atlas = self.write_texture_atlas.isChecked()


class FramesExport(QGroupBox):
    """
    Controls configuration for exporting individual frames as an image sequence.
    """

    base_name = QLineEdit("sprite")

    custom_dir = QCheckBox("Custom directory")
    directory = QLineEdit()
    change_dir = QPushButton(KI.icon("folder"), None)
    reset_dir = QPushButton(KI.icon("view-refresh"), None)

    force_new = QCheckBox("Force new folder")

    def __init__(self):
        super().__init__("Export image sequence")
        self.setCheckable(True)
        self.setChecked(False)

        self.custom_dir.setToolTip("Manually define the images' export directory")
        self.toggle_custom_dir(Qt.Unchecked)
        self.custom_dir.stateChanged.connect(self.toggle_custom_dir)

        self.directory.setToolTip("The directory the images will be exported to")
        self.change_dir.setToolTip("Open a file picker to choose the images directory")
        self.reset_dir.setToolTip("Reset images directory based on the export path")

        self.force_new.setToolTip(
            "If checked, create a new frames folder if one exists.\nOtherwise, write the sprites in the existing folder (may overwrite files)"
        )

        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self.custom_dir)
        dir_layout.addWidget(self.directory)
        dir_layout.addWidget(self.change_dir)
        dir_layout.addWidget(self.reset_dir)

        layout = QFormLayout(self)
        layout.addRow("Base name:", self.base_name)
        layout.addRow(dir_layout)
        layout.addRow(self.force_new)

    def toggle_custom_dir(self, state: int):
        enabled = state == Qt.Checked
        self.directory.setEnabled(enabled)
        self.change_dir.setEnabled(enabled)
        self.reset_dir.setEnabled(enabled)

    def apply_settings(self, exp: SpritesheetExporter):
        if not self.isChecked():
            exp.export_frame_sequence = False
            return

        exp.export_frame_sequence = True
        exp.base_name = self.base_name.text()

        if self.custom_dir.isChecked():
            exp.custom_frames_dir = Path(self.directory.text())
        else:
            exp.custom_frames_dir = None

        exp.force_new = self.force_new.isChecked()


class SpritePlacement(QFormLayout):
    """
    Lets the user choose if they want the spreadsheet horizontally or vertically
    oriented, and how many cells to put in that direction.
    """

    h_dir = QRadioButton("Horizontal")
    v_dir = QRadioButton("Vertical")

    columns = QSpinBox(value=DEFAULT_SPACE, minimum=DEFAULT_SPACE)
    rows = QSpinBox(value=DEFAULT_SPACE, minimum=DEFAULT_SPACE)

    def __init__(self):
        super().__init__()
        self.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.setHorizontalSpacing(12)

        self.h_dir.setChecked(True)
        self.h_dir.setToolTip("Order the sprites horizontally")
        self.v_dir.setToolTip("Order the sprites vertically")

        self.columns.setSpecialValueText("Auto")
        self.columns.setToolTip("Number of columns in the spritesheet")

        self.rows.setEnabled(False)
        self.rows.setSpecialValueText("Auto")
        self.rows.setToolTip("Number of rows in the spritesheet")

        self.h_dir.toggled.connect(self.toggle_horizontal)
        self.v_dir.toggled.connect(self.toggle_vertical)

        col_layout = QFormLayout()
        col_layout.setHorizontalSpacing(4)
        col_layout.addRow("Columns:", self.columns)

        row_layout = QFormLayout()
        row_layout.setHorizontalSpacing(4)
        row_layout.addRow("Rows:", self.rows)

        field = QGridLayout()
        field.addWidget(self.h_dir, 0, 0)
        field.addWidget(self.v_dir, 0, 1)
        field.addLayout(col_layout, 1, 0)
        field.addLayout(row_layout, 1, 1)

        self.addRow("Sprite placement:", field)

    def toggle_horizontal(self, checked: bool):
        self.columns.setEnabled(checked)
        self.rows.setEnabled(not checked)

    def toggle_vertical(self, checked: bool):
        self.columns.setEnabled(not checked)
        self.rows.setEnabled(checked)

    def apply_settings(self, exp: SpritesheetExporter):
        if self.h_dir.isChecked():
            exp.horizontal = True
            exp.size = self.columns.value()
        else:
            exp.horizontal = False
            exp.size = self.rows.value()


class SpinBoxes(QFormLayout):
    start = QSpinBox(minimum=DEFAULT_TIME, maximum=9999)
    end = QSpinBox(minimum=DEFAULT_TIME, maximum=9999)
    step = QSpinBox(value=1, minimum=1)

    def __init__(self):
        super().__init__()

        self.start.setValue(DEFAULT_TIME)
        self.end.setValue(DEFAULT_TIME)

        self.start.setSpecialValueText("Auto")
        self.end.setSpecialValueText("Auto")
        self.step.setSpecialValueText("Auto")

        self.start.setToolTip("First frame time of the animation (inclusive)")
        self.end.setToolTip("Last frame time of the animation (inclusive)")
        self.step.setToolTip(
            "Only export each 'step' number of frames.\nDefaults to every frame"
        )

        self.addRow("Start:", self.start)
        self.addRow("End:", self.end)
        self.addRow("Step:", self.step)

    def apply_settings(self, exp: SpritesheetExporter):
        exp.start = self.start.value()
        exp.end = self.end.value()
        exp.step = self.step.value()


class UISpritesheetExporter:
    exp = SpritesheetExporter()
    dialog = QDialog()  # the main window

    common_settings = CommonSettings()
    frames = FramesExport()

    # Extra settings group
    layers_as_animation = QCheckBox("Use layers as animation frames")
    placement = SpritePlacement()
    spin_boxes = SpinBoxes()

    dialog_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

    def __init__(self):
        self.dialog.setWindowTitle(i18n("SpritesheetExporter"))
        self.dialog.setWindowModality(Qt.NonModal)  # Don't block input to other windows
        self.dialog.setMinimumSize(425, 450)
        self.dialog.setSizeGripEnabled(True)

        self.common_settings.change_dir.clicked.connect(self.change_export_dir)
        self.common_settings.reset_dir.clicked.connect(self.reset_export_dir)

        self.frames.change_dir.clicked.connect(self.change_frames_dir)
        self.frames.reset_dir.clicked.connect(self.reset_frames_dir)

        self.layers_as_animation.setToolTip(
            "Whether to treat each layer as a frame instead of using the animation timeline"
        )

        self.dialog_buttons.accepted.connect(self.confirmButton)
        self.dialog_buttons.rejected.connect(self.dialog.close)

        # Setup layouts
        extra_settings = QGroupBox("Extra Settings")
        extra_settings.setCheckable(True)
        extra_settings.setChecked(False)

        extras = QVBoxLayout(extra_settings)
        extras.addWidget(self.layers_as_animation)
        extras.addSpacing(10)
        extras.addLayout(self.placement)
        extras.addSpacing(10)
        extras.addLayout(self.spin_boxes)

        root_layout = QVBoxLayout(self.dialog)  # the box holding everything
        root_layout.addLayout(self.common_settings)
        root_layout.addWidget(self.frames)
        root_layout.addWidget(extra_settings)
        root_layout.addWidget(self.dialog_buttons)

    def show_dialog(self):
        if self.common_settings.directory.text() == "":
            self.reset_export_dir()
        if self.frames.directory.text() == "":
            self.reset_frames_dir()

        self.dialog.show()
        self.dialog.activateWindow()
        self.dialog.setDisabled(False)

    @staticmethod
    def current_directory() -> Optional[Path]:
        doc = KI.activeDocument()
        if not doc or not doc.fileName():
            return None
        return Path(doc.fileName()).parent

    @staticmethod
    def pick_directory_dialog(directory: str) -> str:
        file_dialog = QFileDialog()
        file_dialog.setWindowTitle(i18n("Choose Export Directory"))
        file_dialog.setSizeGripEnabled(True)

        # QFileDialog already seems to handle invalid directories fine
        file_dialog.setDirectory(directory)

        return file_dialog.getExistingDirectory()

    def change_export_dir(self):
        # Grab the output path on directory changed
        path = UISpritesheetExporter.pick_directory_dialog(
            self.common_settings.directory.text()
        )
        if path != "":
            self.common_settings.directory.setText(path)

    def reset_export_dir(self):
        path = UISpritesheetExporter.current_directory()
        if path:
            self.common_settings.directory.setText(str(path))

    def change_frames_dir(self):
        path = UISpritesheetExporter.pick_directory_dialog(self.frames.directory.text())
        if path != "":
            self.frames.directory.setText(path)

    def reset_frames_dir(self):
        path = UISpritesheetExporter.current_directory()
        if path:
            frames_dir = Path(
                path, self.common_settings.name.text().split(".")[0] + "_sprites"
            )
            self.frames.directory.setText(str(frames_dir))

    def confirmButton(self):
        # Block any function calls on subsequent clicks
        self.dialog.setDisabled(True)

        self.common_settings.apply_settings(self.exp)
        self.frames.apply_settings(self.exp)
        self.placement.apply_settings(self.exp)
        self.spin_boxes.apply_settings(self.exp)
        self.exp.layers_as_animation = self.layers_as_animation.isChecked()

        self.exp.export()
        self.dialog.hide()
