# Blends all linked layers using python (slow)

from traceback import format_exc
from gimpfu import *

MODE_AVERAGE = 0
MODE_DARKEN = 1
MODE_LIGHTEN = 2
MODE_NORMAL_INVERSE = 3
MODE_NORMAL_EXTRACT = 4
MODE_MEDIAN = 5

MODE_NAMES = ['Average','Darken','Lighten','Inverse Normal','Extract Normal','Median']

def get_layers(image, visible=0, linked=0):
  layers = []
  for layer in image.layers:
    if visible and not layer.visible: continue
    if linked and not layer.linked: continue
    layers.append(layer)
  return layers


# Main function
def plugin_main(image, drawable, visible_only, linked_only, blend_mode, edge_crop_h, edge_crop_v, edge_blend_h, edge_blend_v):
  try:
    # Get all linked layers within the specified image or layer group
    parent = pdb.gimp_item_get_parent(drawable)
    if parent is None:
      layers = get_layers(image, visible_only, linked_only)
    else:
      layers = get_layers(parent, visible_only, linked_only)

    # Nothing selected. Cancel.
    if len(layers) <= 0: return

    gimp.progress_init("Blend: Init")
    # Precalculated constant
    edge_total_h = edge_crop_h + edge_blend_h
    edge_total_v = edge_crop_h + edge_blend_v

    # New layer name combining the first and last layer names
    layer_name = layers[-1].name.partition('.')[0] + "-" + layers[0].name.partition('.')[0]

    # Calculate properties of the new layer to be added
    # New layer is the minimum size necessary to contain all linked layers
    new_pos = pdb.gimp_image_get_item_position(image, drawable)
    new_x, new_y = layers[0].offsets
    new_w = new_x + layers[0].width
    new_h = new_y + layers[0].height
    for layer in layers[1:]:
      lx, ly = layer.offsets
      if lx < new_x: new_x = lx
      if ly < new_y: new_y = ly
      lx += layer.width
      ly += layer.height
      if lx > new_w: new_w = lx
      if ly > new_h: new_h = ly
    new_w -= new_x
    new_h -= new_y

    pt = [0.0]*4*new_w*new_h # Total of pixel values
    pc = [0.0, 0.0, 0.0, 1.0]*new_w*new_h # Count of layers applying to each pixel

    # For tracking progress
    layer_no = -1
    layers_total = len(layers)
    mode = blend_mode

    # Iterate each layer, adding their pixel values to the above totals
    for layer in reversed(layers):
      layer_no += 1
      # Set layer weight. Format in the layer name is (w%f) 
      i = 0
      weight = 1.0
      while 1:
        i = layer.name.find('(w', i)
        if i < 0: break
        i += 2
        j = layer.name.find(')', i)
        if j < 0: continue
        try:
          weight = float(layer.name[i:j])
          break
        except:
          pass
      if weight <= 0.0: continue

      pdb.gimp_progress_set_text("Blend: Process layer (%d/%d) (w=%.3f)" % (layer_no + 1, layers_total, weight))

      # Copy layer data into variables for faster access
      lx, ly = layer.offsets
      # Position relative to created layer
      lx -= new_x 
      ly -= new_y
      lw = layer.width
      lh = layer.height
      la = layer.opacity / 100.0
      lha = layer.has_alpha

      # Read pixel data
      pr = layer.get_pixel_rgn(0, 0, lw, lh)
      bpp = pr.bpp
      
      for y in xrange(0, lh):
        pixels = bytearray(pr[:,y])
        gimp.progress_update((layer_no + 1.0 * y / lh) / (layers_total + 1))

        # Crop and/or fade edges to prevent artifacts
        py = ly + y # Position in new layer
        if y < edge_total_v and ly > 0:
          if y < edge_crop_v: continue
          ay = 1.0*(y - edge_crop_v + 1)/(edge_blend_v + 1)
        else:
          ay = 1.0
        if y >= lh - edge_total_v and ly + lh < new_h:
          if y >= lh - edge_crop_v: continue
          az = 1.0*(lh - y - edge_crop_v)/(edge_blend_v + 1)
          if az < ay: ay = az
        for x in xrange(0, lw):
          px = lx + x # Position in new layer
          az = ay
          if x < edge_total_h and lx > 0:
            if x < edge_crop_h:
              continue
            else:
              ax = 1.0*(x - edge_crop_h + 1)/(edge_blend_h + 1)
              if ax < az: az = ax
          if x >= lw - edge_total_h and lx + lw < new_w:
            if x >= lw - edge_crop_h: continue
            ax = 1.0*(lw - x - edge_crop_h)/(edge_blend_h + 1)
            if ax < az: az = ax

          p = pixels[x*bpp:(x+1)*bpp]  # Pixel value [R, G, B, A]
          a = p[-1] if lha else 255.0 # Apply pixel alpha
          a *= la*az*weight
          if a <= 0.0: continue
          af = a/255.0
          n = (px + py*new_w)*4 # Byte offset for this pixel's first channel in new layer

          # No blending applied to the first layer
          if layer_no == 0:
            if mode == MODE_MEDIAN:
              for c in p[:3]:
                pt[n] = bytearray((c,))
                n += 1
            else:
              for c in p[:3]:
                pt[n] = c*af
                pc[n] = af
                n += 1
            pt[n] = a

          ### BLEND
          elif mode == MODE_AVERAGE:
            for c in p[:3]:
              pt[n] += c*af
              pc[n] += af
              n += 1
            if a > pt[n]: pt[n] = a

          ### MEDIAN
          elif mode == MODE_MEDIAN:
            for c in p[:3]:
              if pt[n] == 0.0:
                pt[n] = bytearray((c,))
              else:
                pt[n].append(c)
              n += 1
            if a > pt[n]: pt[n] = a

          ### DARKEN
          elif mode == MODE_DARKEN:
            for c in p[:3]:
              if pc[n] <= 0.0:
                pt[n] = c
                pc[n] = 1.0
              else:
                if c < pt[n]/pc[n]:
                  pt[n] = c*pc[n]
              n += 1
            if a > pt[n]: pt[n] = a

          ### LIGHTEN
          elif mode == MODE_LIGHTEN:
            for c in p[:3]:
              if pc[n] <= 0.0:
                pt[n] = c
                pc[n] = 1.0
              else:
                if c > pt[n]/pc[n]:
                  pt[n] = c*pc[n]
              n += 1
            if a > pt[n]: pt[n] = a

          ### INVERSE NORMAL
          elif mode == MODE_NORMAL_INVERSE:
            if pt[n+3] > 0.0:
              if af >= 1.0: continue
              na = 1.0 - (1.0 - (pt[n+3]/255.0))/af
              if na > 0.0:
                for c in p[:3]:
                  # Add weighted pixel value and layer count
                  pt[n] = (pt[n] - c*af) / (1.0 - af) / na
                  pc[n] = 1.0
                  n += 1
              else:
                n += 3
              #  Set pixel alpha to highest opacity encountered for that pixel
              pt[n] = na*255.0

          ### EXTRACT OVERLAY
          elif mode == MODE_NORMAL_EXTRACT:
            if pt[n+3] > 0.0:
              mc = list(gimp.get_foreground()[:3])
              mm = None
              d = 0
              for i in xrange(0, 3):
                c = pt[n]
                pt[n] = mc[i]
                if abs(mc[i] - c) > d:
                  d = abs(mc[i] - c)
                  mm = 255.0*(p[i] - c)/(mc[i] - c)
                n += 1
              #  Set pixel alpha to highest opacity encountered for that pixel
              if mm is None:
                pt[n] - 0.0
              else:
                pt[n] = mm
    
    # Import pixel data to the new layer
    newlayer = gimp.Layer(image, layer_name, new_w, new_h, RGBA_IMAGE, 100, LAYER_MODE_NORMAL)
    pr = newlayer.get_pixel_rgn(0, 0, new_w, new_h, True)

    pdb.gimp_progress_set_text("Blend: Create layer")
    if mode == MODE_MEDIAN:
      for n in xrange(0, len(pt)):
        p = pt[n]
        if type(p) is bytearray:
          p = list(p)
          p.sort()
          i = len(p)
          if i % 2:
            pt[n] = p[i // 2]
          else:
            i //= 2
            pt[n] = (p[i] + p[i-1] + 1) // 2
          pc[n] = 1.0
      
    xmax = new_w*4
    pixels = bytearray(new_w*4)
    x = 0
    y = 0
    for n in xrange(0, len(pt)):
      if pc[n] > 0.0:
        p = int(pt[n] / pc[n] + 0.5)
        if p > 255: p = 255
        if p < 0: p = 0
        pixels[x] = p
      else:
        pixels[x] = 0
      x += 1
      if x >= xmax:
        # Process one row at a time to abate memory errors
        pr[:,y] = bytes(pixels)
        x = 0
        y += 1
        gimp.progress_update((layers_total + 1.0 * y / new_h) / (layers_total + 1.0))
    
    newlayer.set_offsets(new_x, new_y)
    pdb.gimp_image_insert_layer(image, newlayer, parent, new_pos)
    gimp.displays_flush()
  except:
    pdb.gimp_message(format_exc())

if __name__ == "__main__":
  gettext.install("gimp20-python", gimp.locale_directory, unicode=True)
  register(
    "python_fu_blend_linked",
    "Averages all selected layers.",
    "",
    "Gavin Ward",
    "Gavin Ward",
    "2018",
    "Blend (external)",
    "RGB*",
    [
      (PF_IMAGE, "image", "Input image", None),
      (PF_DRAWABLE, "drawable", "Input drawable", None),
      (PF_TOGGLE, "visible_only", "Visible only", 0),
      (PF_TOGGLE, "linked_only", "Linked only", 1),
      (PF_OPTION, "blend_mode", "Mode", 0, MODE_NAMES),
      (PF_ADJUSTMENT, "edge_crop_h", "Crop H", 0, (0,500,1)),
      (PF_ADJUSTMENT, "edge_crop_v", "Crop V", 0, (0,500,1)),
      (PF_ADJUSTMENT, "edge_blend_h", "Blend H", 0, (0,500,1)),
      (PF_ADJUSTMENT, "edge_blend_v", "Blend V", 0, (0,500,1))
    ],
    [],
    plugin_main,
    menu="<Image>/Linked/Blend",
    domain=("gimp20-python", gimp.locale_directory))
  
  main()
