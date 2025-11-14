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
from .utils import KritaVersion


def _current_directory() -> Optional[Path]:
    doc = Krita.instance().activeDocument()
    return Path(doc.fileName()).parent if doc and doc.fileName() else None


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
    @property
    def api_version(self) -> KritaVersion:
        """Lazy loads an analysis of available Krita API functions"""
        if not hasattr(self, "_api_version"):
            self._api_version = KritaVersion()
        return self._api_version

    def __init__(self):
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

    def export(self):
        path, unique_frames, texture_atlas = self.dialog.main_settings.values()

        Exporter(
            path,
            self.dialog.frames.get_settings(),
            self.dialog.frame_times.values(),
            unique_frames,
            self.dialog.layers_as_animation.isChecked(),
            *self.dialog.placement.values(),
            self.dialog.edges.values(),
            texture_atlas,
            self.api_version,
        ).export()

    def reset_export_dir(self):
        path = _current_directory()
        if path:
            self.dialog.main_settings.directory.setText(str(path))

    def reset_frames_dir(self):
        path = _current_directory()
        if path:
            basename = self.dialog.main_settings.name.text().rsplit(".", 1)[0]
            frames_dir = Path(path, basename + "_sprites")
            self.dialog.frames.directory.setText(str(frames_dir))
