(define (script-fu-generate-alpha image drawable)
    (let* (
        (parent (car (gimp-item-get-parent drawable)))
        (position (car (gimp-image-get-item-position image drawable)))
        (layers 0)
        (drawable2 0)
        (group 0)
        (mask1 0)
        (mask2 0)
        (layer1 0)
        (layer2 0)
        )
        
        ; Get all layers in the same group as the selected layer
        (cond 
            ((= parent -1)
                (set! layers (cadr (gimp-image-get-layers image)))
            )
            (else
                (set! layers (cadr (gimp-item-get-children parent)))
            )
        )
        
        ; Use the selected layer and the one directly below it
        ; If the last layer is selected use the one above it instead
        (if (>= (+ position 1) (vector-length layers))
            (set! position (- position 1))
        )
        (set! drawable (vector-ref layers position))
        (set! drawable2 (vector-ref layers (+ position 1)))
        
        (gimp-image-undo-group-start image)
        
        (set! group (car (gimp-layer-group-new image)))
        (gimp-layer-set-mode group LAYER-MODE-NORMAL-LEGACY)
        (gimp-image-insert-layer image group parent 0)
        
        ; Add working layers to the image
        (gimp-item-set-visible drawable TRUE)
        (gimp-item-set-visible drawable2 TRUE)
        (gimp-layer-set-mode drawable LAYER-MODE-NORMAL-LEGACY)
        (gimp-layer-set-mode drawable2 LAYER-MODE-NORMAL-LEGACY)
        
        (set! mask1 (car (gimp-layer-new-from-drawable drawable image)))
        (set! mask2 (car (gimp-layer-new-from-drawable drawable2 image)))
        (set! layer1 (car (gimp-layer-new-from-drawable drawable image)))
        (set! layer2 (car (gimp-layer-new-from-drawable drawable2 image)))
        
        (gimp-layer-set-mode mask1 LAYER-MODE-DIFFERENCE-LEGACY)
        
        (gimp-image-insert-layer image layer2 group 0)
        (gimp-image-insert-layer image layer1 group 0)
        (gimp-image-insert-layer image mask2 group 0)
        (gimp-image-insert-layer image mask1 group 0)
        
        ; Convert mask layers to an alpha channel
        (set! mask1 (car (gimp-image-merge-down image mask1 CLIP-TO-BOTTOM-LAYER)))
        (gimp-drawable-invert mask1 TRUE)
        (gimp-drawable-desaturate mask1 DESATURATE-VALUE)
        (gimp-drawable-levels-stretch mask1)
        
        ; Apply to the group as a mask
        (set! mask2 (car (gimp-layer-create-mask group ADD-MASK-COPY)))
        (gimp-layer-add-mask group mask2)
        
        ; Adjust the brightness of semi-transparent areas
        (gimp-layer-set-opacity layer1 30.0)
        
        (gimp-image-remove-layer image mask1)
        (gimp-image-remove-layer image drawable)
        (gimp-image-remove-layer image drawable2)
        
        (gimp-image-set-active-layer image group)
        
        (gimp-image-undo-group-end image)
    )
)

(script-fu-register
    "script-fu-generate-alpha"
    "Generate Alpha"
    "Takes two layers with different background colors and generates an alpha channel" ;description
    "Gavin Ward"
    "Gavin Ward"
    "2023/07/05"
    "RGB*"
    SF-IMAGE    "image"    0
    SF-DRAWABLE "drawable" 0
)
(script-fu-menu-register "script-fu-generate-alpha" "<Image>/Colors")

