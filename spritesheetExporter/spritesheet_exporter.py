"""
The backend that handles exporting spritesheet.
"""

from krita import Krita, Document, Node
from builtins import Application

from math import sqrt, ceil
import json
from pathlib import Path

KI = Krita.instance()
DEFAULT_TIME = -1
DEFAULT_SPACE = 0


class SpritesheetExporter:
    export_name = "Spritesheet"
    export_dir = Path.home()

    horizontal = True
    rows = DEFAULT_SPACE
    columns = DEFAULT_SPACE
    start = DEFAULT_TIME
    end = DEFAULT_TIME

    force_new = False
    step = 1
    layers_as_animation = False
    write_texture_atlas = False

    def _position_layer(self, layer: Node, imgNum: int, width: int, height: int):
        distance = self.columns if self.horizontal else self.rows
        layer.move(
            int((imgNum % distance) * width),
            int((imgNum // distance) * height),
        )

    def _check_last_keyframe(self, layer: Node, doc: Document):
        """
        Finds the time of the layer's last keyframe, and updates the upper time limit
        accordingly.

        @param layer A visible and animated layer
        @param doc The document to which the layer belongs to
        """

        frame = doc.fullClipRangeEndTime()

        while not layer.hasKeyframeAtTime(frame) and frame >= 0:
            frame -= 1

        if self.end < frame:
            self.end = frame

    def _check_first_keyframe(self, layer: Node, doc: Document):
        """
        Finds the time of the layer's first keyframe, and updates the lower time limit
        accordingly.

        @param layer A visible and animated layer
        @param doc The document to which the layer belongs to
        """

        frame = 0
        end_time = doc.fullClipRangeEndTime()

        while not layer.hasKeyframeAtTime(frame) and frame <= end_time:
            frame += 1

        if self.start > frame:
            self.start = frame

    # get actual animation duration
    def _set_frame_times(self, doc: Document):
        """
        Updates the lower and upper frame time limits if they are set to default values.

        To avoid unnecessary work, check if either of the time values are default before
        calling this function.
        """

        # only from version 4.2.x on can we use hasKeyframeAtTime;
        # in earlier versions we just export from 0 to 100 as default
        major, minor, _ = Application.version().split(".")
        is_new_version = int(major) > 4 or (int(major) == 4 and int(minor) >= 2)

        # get the last frame smaller than
        # the clip end time (whose default is 100)
        if is_new_version:
            layers = doc.rootNode().findChildNodes("", True)
            filtered_layers = [i for i in layers if i.visible() and i.animated()]

            if self.end == DEFAULT_TIME:
                for layer in filtered_layers:
                    self._check_last_keyframe(layer, doc)

            if self.start == DEFAULT_TIME:
                self.start = self.end
                for layer in filtered_layers:
                    self._check_first_keyframe(layer, doc)
        else:
            if self.end == DEFAULT_TIME:
                self.end = 100
            if self.start == DEFAULT_TIME:
                self.start = 0

    def make_export_path(self, suffix=""):
        return self.export_dir.joinpath(self.export_name + suffix)

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

        num_frames = 0

        if self.layers_as_animation:
            paint_layers = src.rootNode().findChildNodes("", True, False, "paintlayer")
            visible_layers = (i for i in paint_layers if i.visible())

            # export each visible layer
            for i, layer in enumerate(visible_layers):
                clone_layer = dest.createCloneLayer(str(i), layer)
                root.addChildNode(clone_layer, None)
                num_frames += 1
        else:
            if self.end == DEFAULT_TIME or self.start == DEFAULT_TIME:
                self._set_frame_times(src)

            for i in range(self.start, self.end + 1, self.step):
                src.setCurrentTime(i)
                pixel_data = src.pixelData(0, 0, width, height)
                layer = dest.createNode(str(i), "paintlayer")
                layer.setPixelData(pixel_data, 0, 0, width, height)
                root.addChildNode(layer, None)
                num_frames += 1

        return num_frames

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
            self.export_name,
            doc.colorModel(),
            doc.colorDepth(),
            doc.colorProfile(),
            doc.resolution(),
        )

        num_frames = self._copy_frames(doc, sheet)

        # getting a default value for rows and columns
        if self.rows == DEFAULT_SPACE:
            if self.columns == DEFAULT_SPACE:
                self.columns = ceil(sqrt(num_frames))  # square fit

            self.rows = ceil(num_frames / self.columns)
        elif self.columns == DEFAULT_SPACE:
            # Though if I have to guess the number of columns,
            # it may also change the (user-set) number of rows.
            # For example, if you want ten rows from twelve sprites
            # instead of two rows of two and eight of one,
            # you'll have six rows of two
            self.columns = ceil(num_frames / self.rows)
            self.rows = ceil(num_frames / self.columns)

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
        texture_atlas = {"frames": []} if self.write_texture_atlas else None

        for layer in sheet.rootNode().childNodes():
            doc.waitForDone()

            index = int(layer.name())
            self._position_layer(
                layer,
                ((index - self.start) / self.step),
                width,
                height,
            )

            if texture_atlas is not None:
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

        if debug:
            print(f"Saving spritesheet to {self.make_export_path()}")

        sheet.setBatchmode(True)  # so it won't show the export dialog window
        sheet.saveAs(str(self.make_export_path(".png")))

        # refresh canvas so the layers are shown
        sheet.refreshProjection()

        # Show the canvas to the user
        KI.activeWindow().addView(sheet)

        if texture_atlas is not None:
            with open(str(self.make_export_path(".json")), "w") as f:
                json.dump(texture_atlas, f)

        if debug:
            print("All done!")
