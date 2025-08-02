# Krita Spritesheet Exporter

A Krita plugin to export animations as spritesheets.

> [!NOTE]
> This plugin can only support animation timelines on Krita version **4.2.0** or later,
> as that was when the Python animation API was added. Alternatively, you may export
> layers as animation frames.

## Features

- Export only unique frames
- Choose whether to place the sprites horizontally or vertically
- Define the number of columns if placed horizontally, and rows if placed vertically
  - By default, the sprites are fit into a square
- Write a JSON texture atlas
- Export individual frames/sprites as an image sequence
- Define the first frame, last frame, and frame step

### Tips and Tricks

- **To import a spritesheet** to the animation timeline of a new layer:
  - With the spritesheet open, go to `Image > Image Split`
  - Then, in a new file of the same dimensions as one frame, use `File > Import Animation Frames`
- **To merge a spritesheet**:
  - Use `File > Import Animation Frames` to add new sprites
  - Then use `Tools > Scripts > Export as Spritesheet` to export the old and new sprites

## Installation

- **Download the plugin** using the green "Code" button on this page, then click "Download ZIP"
- **Import the plugin into Krita** using one of the following:
  - Open Krita
    - Go to `Tools > Scripts > Import Python Plugin`
    - Select the downloaded ZIP file
  - Extract the ZIP file
    - Find `pykrita` in Krita's resources folder
      - The resources location can be found in `Settings > Configure Krita...`, then
        `General > Resources`
      - Alternatively, you can open the resources folder through
        `Settings > Manage Resources > Open Resources Folder`
    - Move `spritesheetExporter.desktop` and the `spritesheetExporter` folder into `pykrita`
- **Restart Krita** if it was open
- **Activate the plugin**
  - Go to `Settings > Configure Krita > Python Plugin Manager`
  - Check `Spritesheet Exporter`
- **Restart Krita**
- You can now use it through `Tools > Scripts > Export as Spritesheet`!

Check [Manual.html](./spritesheetExporter/Manual.html) for more information.
