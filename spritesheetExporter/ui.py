"""
The UI that displays configuration options to the user with a dialog window.
"""

from krita import Krita
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QButtonGroup,
    QPushButton,
    QSpinBox,
    QDialog,
    QLineEdit,
    QCheckBox,
    QDialogButtonBox,
    QRadioButton,
)
from builtins import i18n
from pathlib import Path

from .exporter import (
    Exporter,
    DEFAULT_SPACE,
    DEFAULT_TIME,
)


class MainSettings(QFormLayout):
    change_dir_clicked = pyqtSignal()
    reset_dir_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        ki = Krita.instance()

        self.name = QLineEdit("spritesheet.png")
        self.name.setToolTip("Name of the exported spritesheet file")

        self.directory = QLineEdit()
        self.directory.setToolTip("Directory to export the spritesheet to")

        change_dir = QPushButton(ki.icon("folder"), None)
        change_dir.setToolTip("Open a file picker for the export directory")
        change_dir.clicked.connect(self.change_dir_clicked.emit)

        reset_dir = QPushButton(ki.icon("view-refresh"), None)
        reset_dir.setToolTip(
            "Reset export directory to the current document's directory"
        )
        reset_dir.clicked.connect(self.reset_dir_clicked.emit)

        self.unique_frames = QCheckBox("Only unique frames")
        self.write_texture_atlas = QCheckBox("Write JSON texture atlas")
        self.write_texture_atlas.setToolTip(
            "Write a JSON texture atlas that can be used in game frameworks (e.g. Phaser 3)"
        )

        dir_layout = QHBoxLayout()
        for w in (self.directory, change_dir, reset_dir):
            dir_layout.addWidget(w)

        self.addRow("Export name:", self.name)
        self.addRow("Export directory:", dir_layout)
        self.addRow(self.unique_frames)
        self.addRow(self.write_texture_atlas)

    def apply_settings(self, exporter: Exporter):
        exporter.export_path = Path(self.directory.text(), self.name.text())
        exporter.unique_frames = self.unique_frames.isChecked()
        exporter.write_texture_atlas = self.write_texture_atlas.isChecked()


class FramesExport(QGroupBox):
    """
    Controls configuration for exporting individual frames as an image sequence.
    """

    change_dir_clicked = pyqtSignal()
    reset_dir_clicked = pyqtSignal()

    def __init__(self):
        super().__init__("Export image sequence")
        self.setCheckable(True)
        self.setChecked(False)
        ki = Krita.instance()

        self.base_name = QLineEdit("sprite")
        self.custom_dir = QCheckBox("Custom directory")

        self.directory = QLineEdit()
        self.directory.setToolTip("Directory the images will be exported to")

        change_dir = QPushButton(ki.icon("folder"), None)
        change_dir.setToolTip("Open a file picker for the images directory")
        change_dir.clicked.connect(self.change_dir_clicked.emit)

        reset_dir = QPushButton(ki.icon("view-refresh"), None)
        reset_dir.setToolTip("Reset images directory based on the export path")
        reset_dir.clicked.connect(self.reset_dir_clicked.emit)

        self.force_new = QCheckBox("Force new folder")
        self.force_new.setToolTip(
            "If checked, create a new frames folder if one exists.\nOtherwise, write the sprites in the existing folder (may overwrite files)"
        )

        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self.custom_dir)

        for w in (self.directory, change_dir, reset_dir):
            w.setEnabled(False)
            self.custom_dir.toggled.connect(w.setEnabled)
            dir_layout.addWidget(w)

        layout = QFormLayout(self)
        layout.addRow("Base name:", self.base_name)
        layout.addRow(dir_layout)
        layout.addRow(self.force_new)

    def apply_settings(self, exporter: Exporter):
        if not self.isChecked():
            exporter.export_frame_sequence = False
            return

        exporter.export_frame_sequence = True
        exporter.base_name = self.base_name.text()

        if self.custom_dir.isChecked():
            exporter.custom_frames_dir = Path(self.directory.text())
        else:
            exporter.custom_frames_dir = None

        exporter.force_new = self.force_new.isChecked()


class SpritePlacement(QFormLayout):
    """
    Lets the user choose if they want the spreadsheet horizontally or vertically
    oriented, and how many cells to put in that direction.
    """

    def __init__(self):
        super().__init__()
        self.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.setHorizontalSpacing(12)

        self.h_dir = QRadioButton("Horizontal")
        self.h_dir.setChecked(True)
        self.h_dir.setToolTip("Order sprites horizontally")

        v_dir = QRadioButton("Vertical")
        v_dir.setToolTip("Order sprites vertically")

        self.size = QSpinBox(value=DEFAULT_SPACE, minimum=DEFAULT_SPACE)
        self.size.setSpecialValueText("Auto")
        self.size.setToolTip("Number of columns or rows in the spritesheet")

        self.columns = QRadioButton("Columns")
        self.columns.setChecked(True)
        rows = QRadioButton("Rows")

        dirs = QVBoxLayout()
        dirs.addWidget(self.h_dir)
        dirs.addWidget(v_dir)
        dirs_buttons = QButtonGroup()
        dirs_buttons.addButton(self.h_dir)
        dirs_buttons.addButton(v_dir)

        sizes = QHBoxLayout()

        size_buttons_box = QVBoxLayout()
        size_buttons_box.addWidget(self.columns)
        size_buttons_box.addWidget(rows)
        size_buttons = QButtonGroup(size_buttons_box)
        size_buttons.addButton(self.columns)
        size_buttons.addButton(rows)

        sizes.addLayout(size_buttons_box)
        sizes.addWidget(self.size)

        self.addRow("Sprite placement:", dirs)
        self.addRow("Spritesheet size:", sizes)

    def apply_settings(self, exporter: Exporter):
        exporter.horizontal = self.h_dir.isChecked()

        if self.columns.isChecked():
            exporter.columns = self.size.value()
            exporter.rows = DEFAULT_SPACE
        else:
            exporter.columns = DEFAULT_SPACE
            exporter.rows = self.size.value()


class SpinBoxes(QFormLayout):
    def __init__(self):
        super().__init__()

        self.start = QSpinBox(value=DEFAULT_TIME, minimum=DEFAULT_TIME, maximum=9999)
        self.end = QSpinBox(value=DEFAULT_TIME, minimum=DEFAULT_TIME, maximum=9999)
        self.step = QSpinBox(value=1, minimum=1)

        for spin_box in (self.start, self.end, self.step):
            spin_box.setSpecialValueText("Auto")

        self.start.setToolTip("First frame time of the animation (inclusive)")
        self.end.setToolTip("Last frame time of the animation (inclusive)")
        self.step.setToolTip(
            "Only export each 'step' numbered frame. Defaults to every frame"
        )

        self.addRow("Start:", self.start)
        self.addRow("End:", self.end)
        self.addRow("Step:", self.step)

    def apply_settings(self, exporter: Exporter):
        exporter.start = self.start.value()
        exporter.end = self.end.value()
        exporter.step = self.step.value()


class EdgePadding(QFormLayout):
    """
    Sets the padding (or clipping) of sprites.
    """

    def __init__(self):
        super().__init__()

        self.left = self._add_spin_box("left")
        self.top = self._add_spin_box("top")
        self.right = self._add_spin_box("right")
        self.bottom = self._add_spin_box("bottom")

    def apply_settings(self, exp: Exporter) -> None:
        exp.pad_left = self.left.value()
        exp.pad_top = self.top.value()
        exp.pad_right = self.right.value()
        exp.pad_bottom = self.bottom.value()

    def _add_spin_box(self, edge: str) -> QSpinBox:
        spin_box = QSpinBox(value=0, minimum=-99, maximum=99)
        spin_box.setSuffix("px")
        spin_box.setToolTip(
            f"Pad the {edge} edge of each sprite, or clip it if negative"
        )

        self.addRow(f"Padding {edge}:", spin_box)
        return spin_box


class Dialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(i18n("SpritesheetExporter"))
        self.setWindowModality(Qt.NonModal)  # Don't block input to other windows
        self.setMinimumSize(425, 480)
        self.setSizeGripEnabled(True)

        self.main_settings = MainSettings()
        self.frames = FramesExport()
        self.edges = EdgePadding()

        # Extra settings group
        self.layers_as_animation = QCheckBox("Use layers as animation frames")
        self.layers_as_animation.setToolTip(
            "Treat each layer as a frame instead of using the animation timeline"
        )
        self.placement = SpritePlacement()
        self.frame_times = SpinBoxes()

        dialog_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        dialog_buttons.accepted.connect(self.accept)
        dialog_buttons.rejected.connect(self.reject)

        # Setup layouts
        spin_boxes = QHBoxLayout()
        spin_boxes.addLayout(self.frame_times)
        spin_boxes.addLayout(self.edges)

        extra_settings = QGroupBox("Extra Settings")
        extra_settings.setCheckable(True)
        extra_settings.setChecked(False)

        extras = QVBoxLayout(extra_settings)
        extras.addWidget(self.layers_as_animation)
        extras.addSpacing(10)
        extras.addLayout(self.placement)
        extras.addSpacing(10)
        extras.addLayout(spin_boxes)

        root_layout = QVBoxLayout(self)  # the box holding everything
        root_layout.addLayout(self.main_settings)
        root_layout.addWidget(self.frames)
        root_layout.addWidget(extra_settings)
        root_layout.addWidget(dialog_buttons)
