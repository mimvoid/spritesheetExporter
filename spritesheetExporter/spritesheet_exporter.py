"""
The backend that handles exporting spritesheet.
"""

from krita import Krita, Document, Node, InfoObject
from builtins import Application
from PyQt5.QtCore import QRect, QByteArray

from collections.abc import Iterable
from typing import Optional
from math import sqrt, ceil
import json
from pathlib import Path

KI = Krita.instance()
DEFAULT_TIME = -1
DEFAULT_SPACE = 0


class SpritesheetExporter:
    export_path: Path
    unique_frames: bool

    horizontal: bool
    size: int
    start: int
    end: int

    export_frame_sequence: bool
    custom_frames_dir: Optional[Path]
    base_name: str
    force_new: bool

    step: int
    layers_as_animation: bool
    write_texture_atlas: bool
    show_export_dialog = False

    def _check_last_keyframe(self, layer: Node, time_range: Iterable[int]):
        """
        Finds the time of the layer's last keyframe, and updates the upper time limit
        accordingly.

        @param layer A visible and animated layer
        @param doc The document to which the layer belongs to
        """

        for time in time_range:
            if layer.hasKeyframeAtTime(time):
                self.end = max(self.end, time)
                return

    def _check_first_keyframe(self, layer: Node, time_range: Iterable[int]):
        """
        Finds the time of the layer's first keyframe, and updates the lower time limit
        accordingly.

        @param layer A visible and animated layer
        @param doc The document to which the layer belongs to
        """

        for time in time_range:
            if layer.hasKeyframeAtTime(time):
                self.start = min(self.start, time)
                return

    # get actual animation duration
    def _set_frame_times(self, doc: Document):
        """
        Updates the lower and upper frame time limits if they are set to default values.
        """

        def_start = self.start == DEFAULT_TIME
        def_end = self.end == DEFAULT_TIME

        if not def_start and not def_end:
            return

        # only from version 4.2.x on can we use hasKeyframeAtTime;
        # in earlier versions we just export from 0 to 100 as default
        major, minor, _ = Application.version().split(".")
        is_new_version = int(major) > 4 or (int(major) == 4 and int(minor) >= 2)

        if is_new_version:
            start_time = doc.fullClipRangeStartTime() if def_start else self.start
            end_time = doc.fullClipRangeEndTime() if def_end else self.end

            if start_time == end_time:
                # The result will just be a single frame, no need for more operations.
                self.start = start_time
                self.end = start_time
                return

            layers = doc.rootNode().findChildNodes("", True)
            filtered_layers = [i for i in layers if i.visible() and i.animated()]

            if not filtered_layers:
                # There are no visible animated layers. In this case, it's fine
                # to just take a single frame at the start
                # TODO: Maybe suggest layers as animation
                self.end = 0
                self.start = 0
                return

            if start_time > end_time:
                start_time, end_time = end_time, start_time  # Swap values
                if self.step > 0:
                    self.step *= -1  # Make the step negative

            if def_end:
                self.end = start_time
                time_range = range(end_time, start_time - 1, -1)
                for layer in filtered_layers:
                    self._check_last_keyframe(layer, time_range)

            if def_start:
                self.start = self.end
                time_range = range(start_time, self.end + 1)
                for layer in filtered_layers:
                    self._check_first_keyframe(layer, time_range)
        else:
            if def_end:
                self.end = 100
            if def_start:
                self.start = 0

    def _make_frames_dir(self):
        if self.custom_frames_dir is None:
            name = self.export_path.stem + "_sprites"
            dir = self.export_path.with_name(name)
        else:
            name = self.custom_frames_dir.name
            dir = self.custom_frames_dir

        if dir.exists():
            if self.force_new:
                export_num = 0
                dir = dir.with_name(name + "0")

                while dir.exists():
                    export_num += 1
                    dir = dir.with_name(name + str(export_num))

                dir.mkdir()
        else:
            dir.mkdir()

        return dir

    def _copy_frames(self, src: Document, dest: Document):
        """
        Copies frames from the source document to the destination.

        @param src The source document
        @param dest The destination document
        """

        root = dest.rootNode()
        width = src.width()
        height = src.height()

        pixel_set: Optional[set[QByteArray]] = set() if self.unique_frames else None

        if self.layers_as_animation:
            paint_layers = src.rootNode().findChildNodes("", True, False, "paintlayer")
            visible_layers = [i for i in paint_layers if i.visible()]

            # export each visible layer
            for i, layer in enumerate(visible_layers):
                if pixel_set is not None:
                    pixel_data = layer.pixelData(0, 0, width, height)
                    if pixel_data in pixel_set:
                        continue  # Got a non-unique frame
                    pixel_set.add(pixel_data)

                clone_layer = dest.createCloneLayer(str(i), layer)
                root.addChildNode(clone_layer, None)
        else:
            if self.end == DEFAULT_TIME or self.start == DEFAULT_TIME:
                self._set_frame_times(src)

            initial_time = src.currentTime()
            frame_range = range(self.start, self.end + 1, self.step)

            for i in frame_range:
                src.setCurrentTime(i)

                # Ensure the time has been set before copying the pixel data
                src.waitForDone()
                pixel_data = src.pixelData(0, 0, width, height)

                if pixel_set is not None:
                    if pixel_data in pixel_set:
                        continue  # Got a non-unique frame
                    pixel_set.add(pixel_data)

                layer = dest.createNode(str(i), "paintlayer")
                layer.setPixelData(pixel_data, 0, 0, width, height)
                root.addChildNode(layer, None)

            src.setCurrentTime(initial_time)  # reset time

    def _process_frames(self, src: Document, dest: Document):
        width = src.width()
        height = src.height()

        frames_dir = self._make_frames_dir() if self.export_frame_sequence else None
        texture_atlas = {"frames": []} if self.write_texture_atlas else None

        for i, layer in enumerate(dest.rootNode().childNodes()):
            if frames_dir is not None:
                file_name = "".join(
                    [self.base_name, str(i).zfill(3), self.export_path.suffix]
                )
                layer.save(
                    str(frames_dir.joinpath(file_name)),
                    dest.xRes(),
                    dest.yRes(),
                    InfoObject(),
                    QRect(0, 0, width, height),
                )

            # Layers are ordered by when they were added, so using `i` is fine
            if self.horizontal:
                x_pos = (i % self.size) * width
                y_pos = (i // self.size) * height
            else:
                x_pos = (i // self.size) * width
                y_pos = (i % self.size) * height

            layer.move(x_pos, y_pos)

            if texture_atlas is not None:
                texture_atlas["frames"].append(
                    {
                        "frame": {
                            "x": x_pos,
                            "y": y_pos,
                            "w": width,
                            "h": height,
                        },
                    }
                )

        if texture_atlas is not None:
            with self.export_path.with_suffix(".json").open("w") as f:
                json.dump(texture_atlas, f)

    def export(self, debug=False):
        """
        Exports sprite animation frames to a new document and positions them
        accordingly.
        """

        doc = KI.activeDocument()
        if not doc:
            return

        if debug:
            print("\nExport spritesheet start.")

        # getting current document info
        # so we can copy it over to the new document
        width = doc.width()
        height = doc.height()

        if self.export_path.suffix == "":
            self.export_path = self.export_path.with_suffix(".png")

        # creating a new document where we'll put our sprites
        sheet = KI.createDocument(
            width,
            height,
            self.export_path.name,
            doc.colorModel(),
            doc.colorDepth(),
            doc.colorProfile(),
            doc.resolution(),
        )

        sheet.setFileName(str(self.export_path))
        sheet.rootNode().setChildNodes([])  # Remove any default layers

        self._copy_frames(doc, sheet)
        num_frames = len(sheet.rootNode().childNodes())

        if self.size == DEFAULT_SPACE:
            # Pack the sprites as densely as possible with a square fit
            self.size = ceil(sqrt(num_frames))
            columns, rows = self.size, self.size
        else:
            # Remove empty sprite cells
            self.size = min(self.size, num_frames)

            columns = self.size
            rows = ceil(num_frames / columns)
            if not self.horizontal:
                columns, rows = rows, columns

        sheet.setWidth(columns * width)
        sheet.setHeight(rows * height)

        if debug:
            print(
                f"new doc name: {sheet.name()}\n"
                + f"old doc width: {width}\n"
                + f"num of frames: {num_frames}\n"
                + f"new doc width: {sheet.width()}"
            )

        # Position frames, and optionally write JSON or export all frames
        self._process_frames(doc, sheet)

        sheet.refreshProjection()  # Refresh canvas to show the layers
        KI.activeWindow().addView(sheet)  # Show the canvas to the user

        if debug:
            print(f"Saving spritesheet to {sheet.fileName()}")

        if not self.show_export_dialog:
            sheet.setBatchmode(True)
        sheet.save()

        major, minor, patch = [int(i) for i in Application.version().split(".")]
        can_set_modify = major > 5 or (
            major == 5 and (minor > 1 or (minor == 1 and patch >= 2))
        )
        if can_set_modify:
            doc.setModified(False)
            if debug:
                print("Removing modified flag from original document")

        if debug:
            print("All done!")
