"""
Connects the backend and the frontend.
"""

from krita import Krita
from builtins import i18n

from PyQt5.QtWidgets import QLineEdit, QFileDialog

from functools import partial
from typing import Optional
from pathlib import Path

from .exporter import Exporter
from .ui import Dialog


def _current_directory() -> Optional[Path]:
    doc = Krita.instance().activeDocument()
    if not doc or not doc.fileName():
        return None
    return Path(doc.fileName()).parent


def _pick_directory_dialog(directory: str) -> str:
    file_dialog = QFileDialog()
    file_dialog.setWindowTitle(i18n("Choose Export Directory"))
    file_dialog.setSizeGripEnabled(True)

    # QFileDialog already seems to handle invalid directories fine
    file_dialog.setDirectory(directory)

    return file_dialog.getExistingDirectory()


def _change_dir(input: QLineEdit):
    # Grab the output path on directory changed
    path = _pick_directory_dialog(input.text())
    if path != "":
        input.setText(path)


class Controller:
    def __init__(self):
        self.exporter = Exporter()
        self.dialog = Dialog()

        self.dialog.main_settings.change_dir_clicked.connect(
            partial(_change_dir, self.dialog.main_settings.directory)
        )
        self.dialog.main_settings.reset_dir_clicked.connect(self.reset_export_dir)

        self.dialog.frames.change_dir_clicked.connect(
            partial(_change_dir, self.dialog.frames.directory)
        )
        self.dialog.frames.reset_dir_clicked.connect(self.reset_frames_dir)
        self.dialog.accepted.connect(self.export)

    def show_dialog(self):
        if self.dialog.main_settings.directory.text() == "":
            self.reset_export_dir()
        if self.dialog.frames.directory.text() == "":
            self.reset_frames_dir()

        self.dialog.show()
        self.dialog.activateWindow()

    def reset_export_dir(self):
        path = _current_directory()
        if path:
            self.dialog.main_settings.directory.setText(str(path))

    def reset_frames_dir(self):
        path = _current_directory()
        if path:
            frames_dir = Path(
                path, self.dialog.main_settings.name.text().split(".")[0] + "_sprites"
            )
            self.dialog.frames.directory.setText(str(frames_dir))

    def export(self):
        self.dialog.main_settings.apply_settings(self.exporter)
        self.dialog.frames.apply_settings(self.exporter)
        self.dialog.placement.apply_settings(self.exporter)
        self.dialog.frame_times.apply_settings(self.exporter)
        self.dialog.edges.apply_settings(self.exporter)
        self.exporter.layers_as_animation = self.dialog.layers_as_animation.isChecked()

        self.exporter.export()
