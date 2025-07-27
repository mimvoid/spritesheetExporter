from krita import Krita, Document, Node, InfoObject
from builtins import i18n, Application
from PyQt5.QtWidgets import QWidget, QMessageBox  # for debug messages

from math import sqrt, ceil
import json
from pathlib import Path  # for path operations (who'd have guessed)

DEFAULT_PATH = Path.home().joinpath("spritesheetExportKritaTmp")
DEFAULT_TIME = -1
DEFAULT_SPACE = 0


class SpritesheetExporter:
    exportName = "Spritesheet"
    exportDir = Path.home()
    spritesExportDir = DEFAULT_PATH

    isHorizontal = True
    rows = DEFAULT_SPACE
    columns = DEFAULT_SPACE
    start = DEFAULT_TIME
    end = DEFAULT_TIME

    forceNew = False
    removeTmp = True
    step = 1
    layersAsAnimation = False
    writeTextureAtlas = False
    layersList: list[Node] = []
    layersStates: list[bool] = []
    offLayers = 0

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

    # - export all frames of the animation in a temporary folder as png
    # - create a new document of the right dimensions
    #   according to self.rows and self.columns
    # - position each exported frame in the new doc according to its name
    # - export the doc (aka the spritesheet)
    # - remove tmp folder if needed
    def export(self, debug=False):
        doc = Krita.instance().activeDocument()
        if not doc:
            return

        def debugPrint(message: str, usingTerminal=True):
            if usingTerminal:
                print(message)
            else:
                QMessageBox.information(QWidget(), i18n("Debug info: "), i18n(message))

        def sheetExportPath(suffix=""):
            return self.exportDir.joinpath(self.exportName + suffix)

        def spritesExportPath(suffix=""):
            return self.spritesExportDir.joinpath(self.exportName + suffix)

        def fileNum(num):
            return "_" + str(num).zfill(3)

        def exportFrame(num):
            doc.waitForDone()
            imagePath = str(spritesExportPath(fileNum(num) + ".png"))
            doc.exportImage(imagePath, InfoObject())
            if debug:
                debugPrint(f"exporting frame {num} at {imagePath}")

        def getLayerState(layer):
            if len(layer.childNodes()) != 0:
                for child in layer.childNodes():
                    getLayerState(child, debug)
            else:
                self.layersStates.append(layer.visible())
                self.layersList.append(layer)
                if not layer.visible():
                    self.offLayers += 1
                if debug:
                    debugPrint(f"saving state {layer.visible()} of layer {layer}")

        if debug:
            debugPrint("\nExport spritesheet start.")

        # clearing lists in case the script is used several times
        # without restarting krita
        self.layersList.clear()
        self.layersStates.clear()
        self.offLayers = 0

        addedFolder = False
        # create a temporary export directory for the individual sprites
        # if the user didn't set any
        if self.spritesExportDir == DEFAULT_PATH:
            self.spritesExportDir = sheetExportPath("_sprites")

        if self.spritesExportDir.exists():
            if self.forceNew:
                # if forceNew, spritesExportDir's value is taken
                # from the user-set choices in the dialog

                exportNum = 0

                parentPath = self.spritesExportDir.parent
                folder = str(self.spritesExportDir.parts[-1])

                def exportCandidate():
                    return parentPath.joinpath(folder + str(exportNum))

                # in case the user has a folder with the exact same name as the temporary one
                while exportCandidate().exists():
                    exportNum += 1
                self.spritesExportDir = exportCandidate()
        else:
            # this will always be called if not forceNew
            # because it will always create a new export folder
            addedFolder = True
            self.spritesExportDir.mkdir()

        doc.setBatchmode(True)  # so it won't show the export dialog window

        if self.layersAsAnimation:
            # save layers state (visible or not)
            layers = doc.topLevelNodes()
            for layer in layers:
                getLayerState(layer, debug)
            framesNum = len(self.layersList)

            # for compatibility between animated frames as frames
            # and layers as frames
            self.start = 0
            self.end = framesNum - 1

            # hide all layers
            for layer in self.layersList:
                layer.setVisible(False)

            # export each visible layer
            for i in range(0, len(self.layersStates), self.step):
                if not self.layersStates[i]:
                    continue
                self.layersList[i].setVisible(True)
                doc.refreshProjection() # refresh the canvas
                exportFrame(i, doc)
                self.layersList[i].setVisible(False)

            # restore layers state
            for i in range(0, len(self.layersStates)):
                self.layersList[i].setVisible(self.layersStates[i])
                if debug:
                    debugPrint(f"restoring layer {i}")
        else:
            # check self.end and self.start values
            # and if needed input default value
            if self.end == DEFAULT_TIME or self.start == DEFAULT_TIME:
                self.setStartEndFrames()
            doc.setCurrentTime(self.start)
            if debug:
                ver = Application.version()
                isNewVersion = int(ver[0]) > 4 or (
                    int(ver[0]) == 4 and int(ver[2]) >= 2
                )
                if isNewVersion:
                    debugPrint(
                        f"animation Length: {doc.animationLength()}; full clip start: {doc.fullClipRangeStartTime()}; full clip end: {doc.fullClipRangeEndTime()}"
                    )
                debugPrint(
                    f"export start: {self.start}; export end: {self.end}; export length: {self.end - self.start}"
                )
            framesNum = ((self.end + 1) - self.start) / self.step

            # export frames
            for i in range(self.start, self.end + 1, self.step):
                exportFrame(i, doc)
                doc.setCurrentTime(i + self.step)

        # getting current document info
        # so we can copy it over to the new document
        width = doc.width()
        height = doc.height()
        col = doc.colorModel()
        depth = doc.colorDepth()
        profile = doc.colorProfile()
        res = doc.resolution()
        # this is very helpful while programming
        # if you're not quite sure what can be done:
        # debugPrint(dir(doc))

        # getting a default value for rows and columns
        if self.rows == DEFAULT_SPACE:
            if self.columns == DEFAULT_SPACE:
                self.columns = ceil(sqrt(framesNum - self.offLayers))  # square fit
            self.rows = ceil((framesNum - self.offLayers) / self.columns)
        elif self.columns == DEFAULT_SPACE:
            # Though if I have to guess the number of columns,
            # it may also change the (user-set) number of rows.
            # For example, if you want ten rows from twelve sprites
            # instead of two rows of two and eight of one,
            # you'll have six rows of two
            self.columns = ceil((framesNum - self.offLayers) / self.rows)
            self.rows = ceil((framesNum - self.offLayers) / self.columns)

        # creating a new document where we'll put our sprites
        sheet = Krita.instance().createDocument(
            self.columns * width,
            self.rows * height,
            self.exportName,
            col,
            depth,
            profile,
            res,
        )

        if debug:
            debugPrint(f"new doc name: {sheet.name()}")
            debugPrint(f"old doc width: {width}")
            debugPrint(f"num of frames: {framesNum}")
            debugPrint(f"new doc width: {sheet.width()}")

            # for debugging when the result of print() is not available
            # QMessageBox.information(QWidget(), i18n("Debug 130"),
            #                         i18n("step: " + str(self.step) +
            #                              "; end: " + str(self.end) +
            #                              "; start: " + str(self.start) +
            #                              "; rows: " + str(self.rows) +
            #                              "; columns: " + str(self.columns) +
            #                              "; frames number: " +
            #                              str(framesNum)))

        # adding our sprites to the new document
        # and moving them to the right position
        root_node = sheet.rootNode()

        # hide the default layer filled with white
        root_node.childNodes()[0].setVisible(False)
        invisibleLayersNum = 0

        textureAtlas = {"frames": []}
        start = 0 if self.layersAsAnimation else self.start

        for i in range(start, self.end + 1, self.step):
            doc.waitForDone()

            if self.layersAsAnimation and not self.layersStates[i]:
                invisibleLayersNum += 1
                continue

            img = str(spritesExportPath(fileNum(i) + ".png"))
            if debug:
                debugPrint(f"managing file {i} at {img}")

            layer = sheet.createFileLayer(img, img, "ImageToSize")
            root_node.addChildNode(layer, None)
            self.positionLayer(
                layer=layer,
                imgNum=(((i - invisibleLayersNum) - self.start) / self.step),
                width=width,
                height=height,
            )

            # refresh canvas so the layers actually do show
            sheet.refreshProjection()

            if self.removeTmp:
                Path(img).unlink()  # removing temporary sprites exports
            if debug:
                debugPrint(
                    f"adding to spritesheet, image {i - self.start} name: {img} at pos: {layer.position()}"
                )
            if self.writeTextureAtlas:
                textureAtlas["frames"].append(
                    {
                        "filename": i,
                        "frame": {
                            "x": layer.position().x(),
                            "y": layer.position().y(),
                            "w": width,
                            "h": height,
                        },
                    }
                )

        # export the document to the export location
        sheet.setBatchmode(True)  # so it won't show the export dialog window
        if debug:
            debugPrint(f"exporting spritesheet to {sheetExportPath()}")

        sheet.exportImage(str(sheetExportPath(".png")), InfoObject())

        if self.writeTextureAtlas:
            with open(str(sheetExportPath(".json")), "w") as f:
                json.dump(textureAtlas, f)

        # and remove the empty tmp folder when you're done
        if self.removeTmp and addedFolder:
            self.spritesExportDir.rmdir()

        if debug:
            debugPrint("All done!")
