### plugin-generate-alpha.py / scm
Generates an alpha channel based on the difference between two images.
Intended use is take two screenshots of a video game object with different background colors to generate an image with a transparent background.
- Pause the game.
- Use a green-screen mod to take a screenshot with a white background.
- Without unpausing, take another screenshot with a black background.
- Place the white layer above the black layer in GIMP.
- Select the white layer, and select Colors > Generate Alpha from the menu.

The backgrounds do not have to be perfectly black or white, but the closer the better.

Note that semi-transparent areas do not perfectly retain the original colors and become less saturated around the edges.
There is currently no intent to fix this - The main use case is generating images to embed in web pages, and the slight color change aids visibility when the transparent object is the same color as the page background.

![Sample](/samples/plugin-generate-alpha.png)

### plugin-linked-operations.py
Automates the linking of multiple layers and performing operations on them.  
This started as a replacement for an old plugin "deep-float-copy.scm" that was used for copy and paste operations.  
I have since added a few other operations as I needed them.
- Link all layers above or below the current layer until an already linked layer is found.
- Cut, copy, paste or delete the contents of a selection for linked layers
- Add or remove linked layers from a group.
- Change linked layers to match the blend mode or opacity of the selected layer.

### plugin-blend-linked.py  
Uses python to blend all linked layers. Note that this runs entirely in python so is very slow.

### plugin-blend-linked-pdb.py  
Uses GIMP operations to blend all linked layers. Much faster than the above.  
Better results for images with with a higher depth than 8bpp. Otherwise slightly worse.

### plugin-select-grid.py
Expands the selection to select all tiles of the grid that have at least one already selected pixel.
