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
