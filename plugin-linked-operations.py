# Automate linking layers and performing various operations on them

from traceback import format_exc
from gimpfu import *
import gtk

def get_layers(image, visible=False, linked=False):
    layers = []
    for layer in image.layers:
        if visible and not layer.visible: continue
        if linked and not layer.linked: continue
        layers.append(layer)
    return layers

def plugin_copy(image, drawable):
    plugin_cut(image, drawable, delete = False)

def plugin_erase(image, drawable):
    plugin_cut(image, drawable, copy = False)

# Copy or cut the selection into new layers for all visible linked layers
def plugin_cut(image, drawable, copy = True, delete = True):
    try:
        # Get all visible linked layers in the currently active group
        parent = pdb.gimp_item_get_parent(drawable)
        layers = get_layers(image if parent is None else parent, linked=True)
        if not layers: return
        pdb.gimp_image_undo_group_start(image)

        # Float the selected area
        for layer in reversed(layers):
            # Sanity checks
            if pdb.gimp_item_get_parent(layer) != parent: continue

            if copy:
                # Create and insert the float layer
                new_layer = pdb.gimp_layer_copy(layer, True)
                new_layer.name = layer.name + "(float)"
                position = pdb.gimp_image_get_item_position(image, layer)
                pdb.gimp_image_insert_layer(image, new_layer, parent, position)

                # Crop out the unselected area
                mask = pdb.gimp_layer_create_mask(new_layer, ADD_MASK_BLACK)
                pdb.gimp_layer_add_mask(new_layer, mask)
                pdb.gimp_edit_fill(mask, FILL_WHITE)
                pdb.gimp_layer_remove_mask(new_layer, MASK_APPLY)

                new_layer.linked = True
                if layer == drawable:
                    drawable = new_layer
            
            # Erase the selected area from the original layer when cutting
            if delete:
                pdb.gimp_edit_clear(layer)
            
            layer.linked = False
            # If the original layer was selected, select the new layer instead

        pdb.gimp_image_set_active_layer(image, drawable)    
        pdb.gimp_image_undo_group_end(image)
    
    except:
        pdb.gimp_message(format_exc())

def plugin_link_up(image, drawable):
    plugin_link(image, drawable, down = False)

def plugin_link_down(image, drawable):
    plugin_link(image, drawable, up = False)

# Link all layers between the current layer and the next linked layer
def plugin_link(image, drawable, down = True, up = True):
    try:
        # Get all visible linked layers in the currently active group
        parent = pdb.gimp_item_get_parent(drawable)
        layers = get_layers(image if parent is None else parent)
        if not layers: return

        affected_layers = []
        i = 0
        for layer in layers:
            if up:
                affected_layers.append(layer)
            if layer == drawable:
                break
            if layer.linked:
                affected_layers = []
            i += 1
        if down:
            link = False
            for layer in layers[i:]:
                if link:
                    if layer.linked:
                        break
                    affected_layers.append(layer)
                elif layer == drawable:
                    if layer not in affected_layers:
                        affected_layers.append(layer)
                    link = True
        if not affected_layers: return

        # Transfer each layer to the new group
        pdb.gimp_image_undo_group_start(image)
        for layer in affected_layers:
            # Sanity checks
            if pdb.gimp_item_get_parent(layer) != parent: continue
            layer.linked = True
        pdb.gimp_image_undo_group_end(image)
    
    except:
        pdb.gimp_message(format_exc())

def plugin_set(image, drawable, getfunc, setfunc):
    try:
        # Get all visible linked layers in the currently active group
        parent = pdb.gimp_item_get_parent(drawable)
        layers = get_layers(image if parent is None else parent, linked=True)
        if not layers: return

        value = getfunc(drawable)
            
        pdb.gimp_image_undo_group_start(image)
        for layer in layers:
            # Sanity checks
            if layer == drawable: continue
            if pdb.gimp_item_get_parent(layer) != parent: continue
            setfunc(layer, value)
        pdb.gimp_image_undo_group_end(image)
    except:
        pdb.gimp_message(format_exc())

# Change the blend mode of all linked layers to match the active layer.
def plugin_set_mode(image, drawable):
    plugin_set(image, drawable, pdb.gimp_layer_get_mode, pdb.gimp_layer_set_mode)

def plugin_set_opacity(image, drawable):
    plugin_set(image, drawable, pdb.gimp_layer_get_opacity, pdb.gimp_layer_set_opacity)
        
# Move all linked layers to outside a group
def plugin_group(image, drawable):
    try:
        # Get all visible linked layers in the currently active group
        parent = pdb.gimp_item_get_parent(drawable)
        layers = get_layers(image if parent is None else parent, linked=True)
        if not layers: return

        # Create the parent group
        pdb.gimp_image_undo_group_start(image)
        group = pdb.gimp_layer_group_new(image)
        group.name = layers[0].name + " Group"
        position = pdb.gimp_image_get_item_position(image, layers[0])
        pdb.gimp_image_insert_layer(image, group, parent, position)

        # Transfer each layer to the new group
        for layer in reversed(layers):
            # Sanity checks
            if pdb.gimp_item_get_parent(layer) != parent: continue

            new_layer = pdb.gimp_layer_copy(layer, False)
            new_layer.name = layer.name
            pdb.gimp_image_remove_layer(image, layer)
            pdb.gimp_image_insert_layer(image, new_layer, group, 0)
            if layer == drawable: drawable = new_layer
        
        pdb.gimp_image_set_active_layer(image, drawable)
        pdb.gimp_image_undo_group_end(image)
    
    except:
        pdb.gimp_message(format_exc())

# Move all linked layers to outside a group
def plugin_ungroup(image, drawable):
    try:
        # Get all visible linked layers in the currently active group
        if pdb.gimp_item_is_group(drawable):
            parent = drawable
        else:
            parent = pdb.gimp_item_get_parent(drawable)
            if parent is None: return
        grandparent = pdb.gimp_item_get_parent(parent)
        layers = get_layers(parent, linked=True)
        if not layers: return

        # Merge the selected layers down.
        pdb.gimp_image_undo_group_start(image)
        for layer in layers:
            # Sanity checks
            if pdb.gimp_item_get_parent(layer) != parent: continue
            new_layer = pdb.gimp_layer_copy(layer, False)
            new_layer.name = layer.name
            pdb.gimp_image_remove_layer(image, layer)
            position = pdb.gimp_image_get_item_position(image, parent)
            pdb.gimp_image_insert_layer(image, new_layer, grandparent, position)
            if layer == drawable: drawable = new_layer
        
        pdb.gimp_image_set_active_layer(image, drawable)
        if len(parent.layers) == 0:
            pdb.gimp_image_remove_layer(image, parent)
        pdb.gimp_image_undo_group_end(image)
    
    except:
        pdb.gimp_message(format_exc())

# Copy the selected layer onto all visible linked layers
def plugin_overlay(image, drawable):
    try:
        # Get all visible linked layers in the currently active group
        parent = pdb.gimp_item_get_parent(drawable)
        parent_layer = image if parent is None else parent
        layers = get_layers(parent_layer, linked=True)
        if not layers: return
        
        # Merge the selected layers down.
        pdb.gimp_image_undo_group_start(image)
        for layer in reversed(layers):
            # Sanity checks
            if pdb.gimp_item_get_parent(layer) != parent: continue
            if layer == drawable: continue
            
            new_layer = pdb.gimp_layer_copy(drawable, True)
            new_layer.visible = True
            layer.visible = True
            position = pdb.gimp_image_get_item_position(image, layer)
            if pdb.gimp_image_get_item_position(image, drawable) > position:
                # Selected layer is background
                pdb.gimp_image_insert_layer(image, new_layer, parent, position + 1)
                layer_name = layer.name
                new_layer = pdb.gimp_image_merge_down(image, layer, EXPAND_AS_NECESSARY)
                new_layer.name = layer_name
            else:
                # Selected layer is foreground
                pdb.gimp_image_insert_layer(image, new_layer, parent, position)
                new_layer = pdb.gimp_image_merge_down(image, new_layer, EXPAND_AS_NECESSARY)
            new_layer.linked = False

        pdb.gimp_image_set_active_layer(image, drawable)
        pdb.gimp_image_undo_group_end(image)
    
    except:
        pdb.gimp_message(format_exc())

# Merge all linked layers down
def plugin_merge(image, drawable):
    try:
        # Get all visible linked layers in the currently active group
        parent = pdb.gimp_item_get_parent(drawable)
        parent_layer = image if parent is None else parent
        layers = get_layers(parent_layer, linked=True)
        if not layers: return
        
        # Merge the selected layers down.
        pdb.gimp_image_undo_group_start(image)
        for layer in reversed(layers):
            # Sanity checks
            if pdb.gimp_item_get_parent(layer) != parent: continue
            
            position = pdb.gimp_image_get_item_position(image, layer) + 1
            if position >= len(parent_layer.layers): continue
            second_layer = parent_layer.layers[position]
            visible = layer.visible or second_layer.visible
            layer.visible = True
            second_layer.visible = True
            new_layer = pdb.gimp_image_merge_down(image, layer, EXPAND_AS_NECESSARY)
            new_layer.linked = True
            new_layer.visible = visible
            # If either of the original layers were selected, select the merged layer
            if (layer == drawable): drawable = new_layer
            if (second_layer == drawable): drawable = new_layer

        pdb.gimp_image_set_active_layer(image, drawable)
        pdb.gimp_image_undo_group_end(image)
    
    except:
        pdb.gimp_message(format_exc())

# Delete all linked layers
def plugin_delete(image, drawable):
    try:
        # Get all visible linked layers in the currently active group
        parent = pdb.gimp_item_get_parent(drawable)
        parent_layer = image if parent is None else parent
        layers = get_layers(parent_layer, linked=True)
        if not layers: return
        
        # Merge the selected layers down.
        pdb.gimp_image_undo_group_start(image)
        for layer in reversed(layers):
            # Sanity checks
            if pdb.gimp_item_get_parent(layer) != parent: continue
            
            position = pdb.gimp_image_get_item_position(image, layer) + 1
            pdb.gimp_image_remove_layer(image, layer)

        pdb.gimp_image_undo_group_end(image)
    
    except:
        pdb.gimp_message(format_exc())

if __name__ == "__main__":
  
    gettext.install("gimp20-python", gimp.locale_directory, unicode=True)

    # name, blurb, help, author, copyright, date, menupath, imagetypes, params, results, function

    register(
        "python_fu_linked_link_down",
        "Link every layer from the active layer to the next linked layer.",
        "",
        "Gavin Ward",
        "Gavin Ward",
        "2020",
        "_Down",
        "*",
        [
          (PF_IMAGE, "image", "Input image", None),
           (PF_DRAWABLE, "drawable", "Input drawable", None)
        ],
        [],
        plugin_link_down,
        menu="<Image>/Li_nked/_Link Set",
        )

    register(
        "python_fu_linked_link_up",
        "Link every layer from the active layer to the previous linked layer.",
        "",
        "Gavin Ward",
        "Gavin Ward",
        "2020",
        "_Up",
        "*",
        [
          (PF_IMAGE, "image", "Input image", None),
           (PF_DRAWABLE, "drawable", "Input drawable", None)
        ],
        [],
        plugin_link_up,
        menu="<Image>/Li_nked/_Link Set",
        )

    register(
        "python_fu_linked_link",
        "Link every layer from the active layer to the nearest linked layers in both directions.",
        "",
        "Gavin Ward",
        "Gavin Ward",
        "2020",
        "_Bidirectional",
        "*",
        [
          (PF_IMAGE, "image", "Input image", None),
           (PF_DRAWABLE, "drawable", "Input drawable", None)
        ],
        [],
        plugin_link,
        menu="<Image>/Li_nked/_Link Set",
        )
    
    register(
        "python_fu_linked_copy",
        "Copy the selection of each linked layer into new layers.",
        "",
        "Gavin Ward",
        "Gavin Ward",
        "2020",
        "_Copy",
        "*",
        [
          (PF_IMAGE, "image", "Input image", None),
           (PF_DRAWABLE, "drawable", "Input drawable", None)
        ],
        [],
        plugin_copy,
        menu="<Image>/Li_nked/_Edit",
        )

    register(
        "python_fu_linked_cut",
        "Move the the selection of each linked layer into new layers.",
        "",
        "Gavin Ward",
        "Gavin Ward",
        "2020",
        "Cut(_x)",
        "*",
        [
            (PF_IMAGE, "image", "Input image", None),
            (PF_DRAWABLE, "drawable", "Input drawable", None)
        ],
        [],
        plugin_cut,
        menu="<Image>/Li_nked/_Edit",
        )

    register(
        "python_fu_linked_erase",
        "Move the the selection of each linked layer into new layers.",
        "",
        "Gavin Ward",
        "Gavin Ward",
        "2020",
        "_Erase",
        "*",
        [
            (PF_IMAGE, "image", "Input image", None),
            (PF_DRAWABLE, "drawable", "Input drawable", None)
        ],
        [],
        plugin_erase,
        menu="<Image>/Li_nked/_Edit",
        )

    register(
        "python_fu_linked_delete",
        "Delete all linked layers.",
        "",
        "Gavin Ward",
        "Gavin Ward",
        "2020",
        "_Delete",
        "*",
        [
            (PF_IMAGE, "image", "Input image", None),
            (PF_DRAWABLE, "drawable", "Input drawable", None)
        ],
        [],
        plugin_delete,
        menu="<Image>/Li_nked/_Layer",
        )

    register(
        "python_fu_linked_merge",
        "Merge each linked layer down onto the layer below.",
        "",
        "Gavin Ward",
        "Gavin Ward",
        "2020",
        "_Merge Down",
        "*",
        [
            (PF_IMAGE, "image", "Input image", None),
            (PF_DRAWABLE, "drawable", "Input drawable", None)
        ],
        [],
        plugin_merge,
        menu="<Image>/Li_nked/_Layer",
        )

    register(
        "python_fu_linked_overlay",
        "Merge each linked layer with the active layer.",
        "",
        "Gavin Ward",
        "Gavin Ward",
        "2020",
        "_Overlay",
        "*",
        [
            (PF_IMAGE, "image", "Input image", None),
            (PF_DRAWABLE, "drawable", "Input drawable", None)
        ],
        [],
        plugin_overlay,
        menu="<Image>/Li_nked/_Layer",
        )

    register(
        "python_fu_linked_group",
        "Move all linked layers to a new group.",
        "",
        "Gavin Ward",
        "Gavin Ward",
        "2020",
        "_Group",
        "*",
        [
            (PF_IMAGE, "image", "Input image", None),
            (PF_DRAWABLE, "drawable", "Input drawable", None)
        ],
        [],
        plugin_group,
        menu="<Image>/Li_nked/_Group",
        )
    
    register(
        "python_fu_linked_ungroup",
        "Move all linked layers out of the selected group.",
        "",
        "Gavin Ward",
        "Gavin Ward",
        "2020",
        "_Ungroup",
        "*",
        [
            (PF_IMAGE, "image", "Input image", None),
            (PF_DRAWABLE, "drawable", "Input drawable", None)
        ],
        [],
        plugin_ungroup,
        menu="<Image>/Li_nked/_Group",
        )

    register(
        "python_fu_linked_set_mode",
        "Change the blend mode of all linked layers to match the active layer.",
        "",
        "Gavin Ward",
        "Gavin Ward",
        "2020",
        "_Mode",
        "*",
        [
            (PF_IMAGE, "image", "Input image", None),
            (PF_DRAWABLE, "drawable", "Input drawable", None)
        ],
        [],
        plugin_set_mode,
        menu="<Image>/Li_nked/_Match",
        )

    register(
        "python_fu_linked_set_opacity",
        "Change the alpha of all linked layers to match the active layer.",
        "",
        "Gavin Ward",
        "Gavin Ward",
        "2020",
        "_Opacity",
        "*",
        [
            (PF_IMAGE, "image", "Input image", None),
            (PF_DRAWABLE, "drawable", "Input drawable", None)
        ],
        [],
        plugin_set_opacity,
        menu="<Image>/Li_nked/_Match",
        )
      
    main()
