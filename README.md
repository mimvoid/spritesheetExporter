# Krita Spritesheet Exporter

krita plugin using the Krita python script manager; it works best using Krita 4.2.x or later. With
earlier Krita 4.x versions, it will work but you won't get the automatic animation length detection; it
gives an error and won't run at 3.x if I recall correctly.

**Exports to a spritesheet** from the animation timeline (using all visible layers) (the spritesheet's
number of rows and columns are user-defined; default is Best Fit (trying to form a square))

- **To import a spritesheet** to the animation timeline of a new layer, simply (with your spritesheet
  open) go to `Image > Image Split` then (in a new file of the same dimensions as one frame), `File > Import Animation Frames`
- **To merge spritesheet**, go to `File > Import Animation Frames` and then `Tools > Scripts > Export as
Spritesheet`

## Installation

- **Download the script** using the green "clone or download" button on this page, then clicking
  "download as zip"
- **Import the plugin into Krita**, by either:
  - Opening krita, going to `Tools > Scripts > Import Python Plugin`, then selecting the zip file you
    downloaded, and clicking Ok into the next dialog box
  - Extracting the .zip and putting both the `spritesheetExporter.desktop` file and the `spritesheetExporter`
    subfolder into the `pykrita` folder in krita's resources folder (that you can find through `Settings >
Manage Resources > Open Resources Folder`)
- **Restart Krita** if it was open
- **Activate the plugin** by going to `Settings > Configure Krita > Python Plugin Manager` and checking
  `Spritesheet Exporter` (if Krita was open, you may need to restart it to see the script in the list, I'm
  not sure)
- **Restart Krita**
- you can now use it in `Tools > Scripts > Export as Spritesheet`

Check the [Manual.html](./spritesheetExporter/Manual.html) page for more information.
