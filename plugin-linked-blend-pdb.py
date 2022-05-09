# Blends all linked layers using GIMP operations only

from traceback import format_exc
from gimpfu import *

CROP = 0

def get_linked_layers(image):
  layers = []
  for layer in image.layers:
    if layer.visible: pdb.gimp_item_set_visible(layer, 0)
    if pdb.gimp_item_is_group(layer):
      continue
    if layer.linked:
      layers.append(layer)
  return layers

def plugin_blend(image, drawable):
  plugin_main(image, drawable, 1)

def crop_by(image, layer, amount):
  if amount <= 0: return
  pdb.gimp_image_select_item(image, CHANNEL_OP_REPLACE, layer)
  pdb.gimp_selection_shrink(image, amount)
  x0, y0 = pdb.gimp_drawable_offsets(layer)
  non_empty, x1, y1, x2, y2 = pdb.gimp_selection_bounds(image)
  pdb.gimp_layer_resize(layer, x2-x1, y2-y1, x0-x1, y0-y1)

def plugin_main(image, drawable, copy=0, shuffle=1, alpharate=1.0):
  try:
    parent = pdb.gimp_item_get_parent(drawable)
    layers = get_linked_layers(image if parent is None else parent)
    if len(layers) < 2:
      return
    layer_name = layers[-1].name.partition('.')[0] + "-" + layers[0].name.partition('.')[0]
    pdb.gimp_image_undo_group_start(image)

    alphafactor = 1.0
    new_layer = pdb.gimp_layer_copy(layers[0], 1)
    pdb.gimp_image_insert_layer(image, new_layer, parent, 0)
    pdb.gimp_item_set_visible(new_layer, 1)
    pdb.gimp_layer_set_opacity(new_layer, 100.0)

    crop_by(image, new_layer, CROP)
    
    del(layers[0])
    i = 0
    while len(layers) > 0:
      if shuffle:
        i = -1 - i
      layer = layers[i]
      del(layers[i])
      
      alphafactor += alpharate
      layer1 = pdb.gimp_layer_copy(layer, 1)
      pdb.gimp_layer_set_opacity(layer1, 100.0)
      pdb.gimp_item_set_visible(layer1, 1)
      pdb.gimp_image_insert_layer(image, layer1, parent, 1)
      crop_by(image, layer1, CROP)
      
      new_layer = pdb.gimp_image_merge_down(image, new_layer, 0)
      

      if alphafactor <= 256.0:
        layer1 = pdb.gimp_layer_copy(layer, 1)
        layer_mode = pdb.gimp_layer_get_mode(layer1)
        pdb.gimp_layer_set_opacity(layer1, 100.0/alphafactor)
        pdb.gimp_item_set_visible(layer1, 1)
        pdb.gimp_image_insert_layer(image, layer1, parent, 0)

        crop_by(image, layer1, CROP)

        new_layer = pdb.gimp_image_merge_down(image, layer1, 0)
        pdb.gimp_layer_set_mode(new_layer, layer_mode)
    pdb.gimp_item_set_name(new_layer, layer_name)
    pdb.gimp_image_undo_group_end(image)
    
  except:
    pdb.gimp_message(format_exc())

if __name__ == "__main__":
  
  gettext.install("gimp20-python", gimp.locale_directory, unicode=True)

  register(
    "python_fu_blend_linked_normal",
    "Averages all linked layers.",
    "",
    "Gavin Ward",
    "Gavin Ward",
    "2017",
    "Blend linked (overlay)",
    "RGB*, GRAY*",
    [(PF_IMAGE, "image", "Input image", None), (PF_DRAWABLE, "drawable", "Input drawable", None)],
    [],
    plugin_blend,
    menu="<Image>/Linked/Blend",
    domain=("gimp20-python", gimp.locale_directory))
    
  main()
