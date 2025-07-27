from krita import Krita, Document, Node
from builtins import Application

from math import sqrt, ceil
import json
from pathlib import Path  # for path operations (who'd have guessed)

DEFAULT_TIME = -1
DEFAULT_SPACE = 0


class SpritesheetExporter:
    exportName = "Spritesheet"
    exportDir = Path.home()

    isHorizontal = True
    rows = DEFAULT_SPACE
    columns = DEFAULT_SPACE
    start = DEFAULT_TIME
    end = DEFAULT_TIME

    forceNew = False
    step = 1
    layersAsAnimation = False
    writeTextureAtlas = False

    def positionLayer(self, layer: Node, imgNum: int, width: int, height: int):
        distance = self.columns if self.isHorizontal else self.rows
        layer.move(
            int((imgNum % distance) * width),
            int((imgNum // distance) * height),
        )

    def checkLayer(self, layer: Node, doc: Document, start: bool):
        if not layer.visible():
            return

        if layer.animated():
            if start:
                frame = 0
                while not (
                    layer.hasKeyframeAtTime(frame) or frame > doc.fullClipRangeEndTime()
                ):
                    frame += 1
                if self.start > frame:
                    self.start = frame
            else:
                frame = doc.fullClipRangeEndTime()
                while not (layer.hasKeyframeAtTime(frame) or frame < 0):
                    frame -= 1
                if self.end < frame:
                    self.end = frame

        # if it was a group layer, we also check its children
        for child in layer.childNodes():
            self.checkLayer(child, doc, start)

    def checkLayerEnd(self, layer: Node, doc: Document):
        self.checkLayer(layer, doc, False)

    def checkLayerStart(self, layer: Node, doc: Document):
        self.checkLayer(layer, doc, True)

    # get actual animation duration
    def setStartEndFrames(self):
        doc = Krita.instance().activeDocument()
        if not doc:
            return

        layers = doc.topLevelNodes()

        # only from version 4.2.x on can we use hasKeyframeAtTime;
        # in earlier versions we just export from 0 to 100 as default
        major, minor, _ = Application.version().split(".")
        isNewVersion = int(major) > 4 or (int(major) == 4 and int(minor) >= 2)

        # get the last frame smaller than
        # the clip end time (whose default is 100)
        if self.end == DEFAULT_TIME:
            if isNewVersion:
                for layer in layers:
                    self.checkLayerEnd(layer, doc)
            else:
                self.end = 100
        # get first frame of all visible layers
        if self.start == DEFAULT_TIME:
            if isNewVersion:
                self.start = self.end
                for layer in layers:
                    self.checkLayerStart(layer, doc)
            else:
                self.start = 0


    def sheetExportPath(self, suffix=""):
        return self.exportDir.joinpath(self.exportName + suffix)

    def _copy_frames(self, src: Document, dest: Document) -> int:
        root = dest.rootNode()
        width = src.width()
        height = src.height()

        num_frames = 0

        if self.layersAsAnimation:
            paint_layers = src.rootNode().findChildNodes(
                recursive=True, type="paintlayer"
            )

            # export each visible layer
            for i, layer in enumerate(paint_layers):
                if not layer.visible():
                    continue

                clone_layer = dest.createCloneLayer(str(i), layer)
                root.addChildNode(clone_layer, None)
                num_frames += 1
        else:
            # check self.end and self.start values
            # and if needed input default value
            if self.end == DEFAULT_TIME or self.start == DEFAULT_TIME:
                self.setStartEndFrames()

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
        - create a new document of the right dimensions
          according to self.rows and self.columns
        - position each exported frame in the new doc according to its name
        - export the doc (aka the spritesheet)
        - remove tmp folder if needed
        """

        doc = Krita.instance().activeDocument()
        if not doc:
            return

        if debug:
            print("\nExport spritesheet start.")

        doc.setBatchmode(True)  # so it won't show the export dialog window

        # getting current document info
        # so we can copy it over to the new document
        width = doc.width()
        height = doc.height()

        # creating a new document where we'll put our sprites
        sheet = Krita.instance().createDocument(
            width,
            height,
            self.exportName,
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
        textureAtlas = {"frames": []}

        for layer in sheet.rootNode().childNodes():
            doc.waitForDone()

            index = int(layer.name())
            self.positionLayer(
                layer,
                ((index - self.start) / self.step),
                width,
                height,
            )

            if self.writeTextureAtlas:
                textureAtlas["frames"].append(
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
            print(f"Saving spritesheet to {self.sheetExportPath()}")

        sheet.setBatchmode(True)  # so it won't show the export dialog window
        sheet.saveAs(str(self.sheetExportPath(".png")))

        # refresh canvas so the layers are shown
        sheet.refreshProjection()

        # Show the canvas to the user
        Krita.instance().activeWindow().addView(sheet)

        if self.writeTextureAtlas:
            with open(str(self.sheetExportPath(".json")), "w") as f:
                json.dump(textureAtlas, f)

        if debug:
            print("All done!")
