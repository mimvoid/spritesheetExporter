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


class Controller:
    exporter = Exporter()
    dialog = Dialog()

    def __init__(self):
        self.dialog.common_settings.change_dir.clicked.connect(
            partial(self.change_dir, self.dialog.common_settings.directory)
        )
        self.dialog.common_settings.reset_dir.clicked.connect(self.reset_export_dir)

        self.dialog.frames.change_dir.clicked.connect(
            partial(self.change_dir, self.dialog.frames.directory)
        )
        self.dialog.frames.reset_dir.clicked.connect(self.reset_frames_dir)
        self.dialog.dialog_buttons.accepted.connect(self.confirm_button)

    def show_dialog(self):
        if self.dialog.common_settings.directory.text() == "":
            self.reset_export_dir()
        if self.dialog.frames.directory.text() == "":
            self.reset_frames_dir()

        self.dialog.show()
        self.dialog.activateWindow()
        self.dialog.setDisabled(False)

    @staticmethod
    def current_directory() -> Optional[Path]:
        doc = Krita.instance().activeDocument()
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

    @staticmethod
    def change_dir(input: QLineEdit):
        # Grab the output path on directory changed
        path = Controller.pick_directory_dialog(input.text())
        if path != "":
            input.setText(path)

    def reset_export_dir(self):
        path = Controller.current_directory()
        if path:
            self.dialog.common_settings.directory.setText(str(path))

    def reset_frames_dir(self):
        path = Controller.current_directory()
        if path:
            frames_dir = Path(
                path, self.dialog.common_settings.name.text().split(".")[0] + "_sprites"
            )
            self.dialog.frames.directory.setText(str(frames_dir))

    def confirm_button(self):
        # Block any function calls on subsequent clicks
        self.dialog.setDisabled(True)

        self.dialog.common_settings.apply_settings(self.exporter)
        self.dialog.frames.apply_settings(self.exporter)
        self.dialog.placement.apply_settings(self.exporter)
        self.dialog.frame_times.apply_settings(self.exporter)
        self.dialog.edges.apply_settings(self.exporter)
        self.exporter.layers_as_animation = self.dialog.layers_as_animation.isChecked()

        self.exporter.export()
        self.dialog.hide()
