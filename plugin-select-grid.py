# Expands the selection to fill all grid tiles with at least one pixel selected

from array import array
from traceback import format_exc
from gimpfu import *

def plugin_main(image, drawable, border=0):
  try:
    if pdb.gimp_selection_is_empty(image):
      return

    
    pdb.gimp_image_undo_group_start(image)
    gx, gy = pdb.gimp_image_grid_get_offset(image)
    gw, gh = pdb.gimp_image_grid_get_spacing(image)
    gx = int(gx)
    gy = int(gy)
    gw = int(gw)
    gh = int(gh)
    selection = image.selection
    bounds, x1, y1, x2, y2 = pdb.gimp_selection_bounds(image)

    sx1 = int((x1 - gx) // gw * gw + gx)
    sy1 = int((y1 - gy) // gh * gh + gy)
    sw = (x2 - sx1 + gw - 1) // gw * gw
    sh = (y2 - sy1 + gh - 1) // gh * gh

    iw = image.width
    ih = image.height
    selection = bytearray(image.selection.get_pixel_rgn(0, 0, iw, ih, 0, 0)[:,:])
    bh = gh
    gimp.progress_init("Select grid")
    pdb.gimp_progress_set_text("Select grid: Processing")
    for by in xrange(sy1, sy1+sh, gh):
      pdb.gimp_progress_update(float(by-sy1) / sh)
      if ih - by < bh: bh = ih - by
      bw = gw
      for bx in xrange(sx1, sx1+sw, gw):
        if iw - bx < bw: bw = iw - bx
        n = by * iw + bx
        nn = n + border * (iw + 1)
        for y in xrange(0, bh - border * 2):
          if selection[nn:nn+bw - border * 2].count(b'\x00') < bw - border * 2:
            nn = n
            for y in xrange(0, bh):
              selection[nn:nn+bw] = b'\xFF'*bw
              nn += iw
            break
          nn += iw
        else:
          nn = n
          for y in xrange(0, bh):
            selection[nn:nn+bw] = b'\x00'*bw
            nn += iw
    pdb.gimp_progress_set_text("Select grid: Applying")
    pdb.gimp_progress_update(1.0)
    pdb.gimp_selection_none(image)
    selection_w = image.selection.get_pixel_rgn(0, 0, image.width, image.height, 1, 1)
    selection_w[:,:] = bytes(selection)
    image.selection.merge_shadow()
    gimp.displays_flush()
    pdb.gimp_image_undo_group_end(image)
    
  except:
    pdb.gimp_message(format_exc())

if __name__ == "__main__":
  
  gettext.install("gimp20-python", gimp.locale_directory, unicode=True)

  register(
    "python_fu_select_grid",
    "Selects all tiles of a given size where at least one pixel is already selected.",
    "",
    "Gavin Ward",
    "Gavin Ward",
    "2017",
    "Selection to Grid",
    "*",
    [(PF_IMAGE, "image", "Input image", None), (PF_DRAWABLE, "drawable", "Input drawable", None)],
    [],
    plugin_main,
    menu="<Image>/Select",
    domain=("gimp20-python", gimp.locale_directory))
    
  main()
