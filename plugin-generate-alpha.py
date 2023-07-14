from traceback import format_exc
from gimpfu import *
import gtk

# Main function
def plugin_main(image, drawable):
  try:
    # Get all linked layers within the specified image or layer group
    parent = pdb.gimp_item_get_parent(drawable)
    position = pdb.gimp_image_get_item_position(image, drawable)
    
    layers = (parent or image).layers
    if position + 1 < len(layers):
      drawable2 = layers[position + 1]
    elif position > 0:
      drawable2 = drawable
      position -= 1
      drawable = layers[position]
    else:
      return

    pdb.gimp_image_undo_group_start(image)
    
    group = pdb.gimp_layer_group_new(image)
    group.mode = LAYER_MODE_NORMAL_LEGACY
    pdb.gimp_image_insert_layer(image, group, parent, position)

    # Add working layers to the image
    mask1 = pdb.gimp_layer_new_from_drawable(drawable, image)
    mask2 = pdb.gimp_layer_new_from_drawable(drawable2, image)
    layer1 = pdb.gimp_layer_new_from_drawable(drawable, image)
    layer2 = pdb.gimp_layer_new_from_drawable(drawable2, image)
    for layer in (layer2, layer1, mask2, mask1):
      layer.visible = True
      layer.mode = LAYER_MODE_NORMAL_LEGACY
      pdb.gimp_image_insert_layer(image, layer, group, position)

    # Convert mask layers to an alpha channel
    pdb.gimp_layer_set_mode(mask1, LAYER_MODE_DIFFERENCE_LEGACY)
    layer = pdb.gimp_image_merge_down(image, mask1, CLIP_TO_BOTTOM_LAYER)
    pdb.gimp_drawable_invert(layer, True)
    pdb.gimp_drawable_desaturate(layer, DESATURATE_VALUE)
    pdb.gimp_drawable_levels_stretch(layer)

    # Apply to the group as a mask
    mask = pdb.gimp_layer_create_mask(group, ADD_MASK_COPY)
    pdb.gimp_layer_add_mask(group, mask)

    # Adjust the brightness of semi-transparent areas
    layer1.opacity = 30.0
    
    pdb.gimp_image_remove_layer(image, layer)
    pdb.gimp_image_remove_layer(image, drawable)
    pdb.gimp_image_remove_layer(image, drawable2)
      
    pdb.gimp_image_undo_group_end(image)
  except:
    pdb.gimp_message(format_exc())

if __name__ == "__main__": # invoked at top level, from GIMP
  gettext.install("gimp20-python", gimp.locale_directory, unicode=True)
  register(
    "python_fu_generate_alpha",  # <= procedure name
    "Takes two layers with different background colors and generates an alpha channel.", # <= blurb
    "",
    "Gavin Ward",
    "Gavin Ward",
    "2023/07/04",
    "Generate Alpha",  # <= menu item
    "RGB*", # <= image type
    [(PF_IMAGE, "image", "Input image", None), (PF_DRAWABLE, "drawable", "Input drawable", None)], # <= hidden and deferred parameters
    [],
    plugin_main,
    menu="<Image>/Colors", # <= menu path
    domain=("gimp20-python", gimp.locale_directory))
  
  main()
