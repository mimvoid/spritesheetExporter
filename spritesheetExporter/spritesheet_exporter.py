"""
The backend that handles exporting spritesheet.
"""

from krita import Krita, Document, Node
from builtins import Application

from collections.abc import Iterable
from math import sqrt, ceil
import json
from pathlib import Path

KI = Krita.instance()
DEFAULT_TIME = -1
DEFAULT_SPACE = 0


class SpritesheetExporter:
    export_name = "spritesheet"
    export_dir = Path.home()

    horizontal = True
    rows = DEFAULT_SPACE
    columns = DEFAULT_SPACE
    start = DEFAULT_TIME
    end = DEFAULT_TIME

    export_individual_frames = True
    force_new = False
    step = 1
    layers_as_animation = False
    write_texture_atlas = False
    show_export_dialog = False

    def _check_last_keyframe(self, layer: Node, time_range: Iterable[int]):
        """
        Finds the time of the layer's last keyframe, and updates the upper time limit
        accordingly.

        @param layer A visible and animated layer
        @param doc The document to which the layer belongs to
        """

        for frame in time_range:
            if layer.hasKeyframeAtTime(frame):
                if self.end < frame:
                    self.end = frame
                return

    def _check_first_keyframe(self, layer: Node, time_range: Iterable[int]):
        """
        Finds the time of the layer's first keyframe, and updates the lower time limit
        accordingly.

        @param layer A visible and animated layer
        @param doc The document to which the layer belongs to
        """

        for frame in time_range:
            if layer.hasKeyframeAtTime(frame):
                if self.start > frame:
                    self.start = frame
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

    def make_export_path(self, suffix=""):
        return self.export_dir.joinpath(self.export_name + suffix)

    def _make_frames_dir(self):
        frames_dir = self.make_export_path("_sprites")

        if frames_dir.exists():
            if self.force_new:
                export_num = 0

                def export_candidate():
                    return self.make_export_path("_sprites" + str(export_num))

                while export_candidate().exists():
                    export_num += 1
                frames_dir = export_candidate()
                frames_dir.mkdir()
        else:
            frames_dir.mkdir()

        return frames_dir

    def _copy_frames(self, src: Document, dest: Document) -> int:
        """
        Copies frames from the source document to the destination.

        @param src The source document
        @param dest The destination document
        @returns The number of frames copied
        """

        root = dest.rootNode()
        width = src.width()
        height = src.height()

        if self.layers_as_animation:
            paint_layers = src.rootNode().findChildNodes("", True, False, "paintlayer")
            visible_layers = [i for i in paint_layers if i.visible()]

            # export each visible layer
            for i, layer in enumerate(visible_layers):
                clone_layer = dest.createCloneLayer(str(i), layer)
                root.addChildNode(clone_layer, None)

            return len(visible_layers)

        if self.end == DEFAULT_TIME or self.start == DEFAULT_TIME:
            self._set_frame_times(src)

        frame_range = range(self.start, self.end + 1, self.step)
        for i in frame_range:
            src.setCurrentTime(i)
            layer = dest.createNode(str(i), "paintlayer")
            root.addChildNode(layer, None)

            # Ensure the time has been set before copying the pixel data
            src.waitForDone()
            pixel_data = src.pixelData(0, 0, width, height)
            layer.setPixelData(pixel_data, 0, 0, width, height)

        return len(frame_range)

    def _process_frames(self, src: Document, dest: Document):
        width = src.width()
        height = src.height()
        num_cells = self.columns if self.horizontal else self.rows

        frames_dir = self._make_frames_dir() if self.export_individual_frames else None
        texture_atlas = {"frames": []} if self.write_texture_atlas else None

        for layer in dest.rootNode().childNodes():
            name = layer.name()

            if frames_dir is not None:
                file_name = f"sprite_{name.zfill(3)}.png"
                new_doc = KI.createDocument(
                    width,
                    height,
                    file_name,
                    src.colorModel(),
                    src.colorDepth(),
                    src.colorProfile(),
                    src.resolution(),
                )

                # Copy the layer
                export_layer = new_doc.createCloneLayer(name, layer)
                new_doc.rootNode().setChildNodes([export_layer])

                # Save the new document
                new_doc.setBatchmode(True)
                new_doc.saveAs(str(frames_dir.joinpath(file_name)))

            # TODO: This is too simple for edge cases, like when the direction
            # is horizontal and there are 7 frames, 2 columns, and 5 rows
            # (there are not enough frames to fill out all 5 rows if they're
            # simply placed horizontally and wrap onto the next row when needed)
            if self.layers_as_animation:
                index = int(name)
            else:
                index = (int(name) - self.start) // self.step

            layer.move(
                (index % num_cells) * width,
                (index // num_cells) * height,
            )

            if texture_atlas is not None:
                dest.waitForDone()
                texture_atlas["frames"].append(
                    {
                        "frame": {
                            "x": layer.position().x(),
                            "y": layer.position().y(),
                            "w": width,
                            "h": height,
                        },
                    }
                )

        if texture_atlas is not None:
            with open(str(self.make_export_path(".json")), "w") as f:
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

        # creating a new document where we'll put our sprites
        sheet = KI.createDocument(
            width,
            height,
            self.export_name + ".png",
            doc.colorModel(),
            doc.colorDepth(),
            doc.colorProfile(),
            doc.resolution(),
        )

        sheet.setFileName(str(self.make_export_path(".png")))
        num_frames = self._copy_frames(doc, sheet)

        # getting a default value for rows and columns
        if self.rows == DEFAULT_SPACE:
            if self.columns == DEFAULT_SPACE:
                self.columns = ceil(sqrt(num_frames))  # square fit

            self.rows = ceil(num_frames / self.columns)
        elif self.columns == DEFAULT_SPACE:
            self.columns = ceil(num_frames / self.rows)

        sheet.setWidth(self.columns * width)
        sheet.setHeight(self.rows * height)

        if debug:
            print(
                f"new doc name: {sheet.name()}\n"
                + f"old doc width: {width}\n"
                + f"num of frames: {num_frames}\n"
                + f"new doc width: {sheet.width()}"
            )

        # Remove the default Background layer
        sheet.rootNode().childNodes()[0].remove()

        # Position frames, and optionally write JSON or export all frames
        self._process_frames(doc, sheet)

        sheet.refreshProjection()  # Refresh canvas to show the layers
        KI.activeWindow().addView(sheet)  # Show the canvas to the user

        if debug:
            print(f"Saving spritesheet to {sheet.fileName()}")

        if not self.show_export_dialog:
            sheet.setBatchmode(True)
        sheet.save()

        if debug:
            print("All done!")
