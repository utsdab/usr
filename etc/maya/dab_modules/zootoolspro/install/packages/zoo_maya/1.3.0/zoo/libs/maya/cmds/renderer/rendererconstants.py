ARNOLD = "Arnold"
REDSHIFT = "Redshift"
RENDERMAN = "Renderman"
VIEWPORT2 = "Viewport"

RENDERER_SUFFIX = {ARNOLD: "ARN",
                   REDSHIFT: "RS",
                   RENDERMAN: "PXR"
                   }

RENDERER_NICE_NAMES = [ARNOLD, REDSHIFT, RENDERMAN]
ALL_RENDERER_NAMES = RENDERER_NICE_NAMES + [VIEWPORT2]

DFLT_RNDR_MODES = [("arnold", ARNOLD), ("redshift", REDSHIFT), ("renderman", RENDERMAN)]  # icon, nicename

RENDERER_SUFFIX_DICT = dict(RENDERER_SUFFIX)
RENDERER_SUFFIX_DICT[VIEWPORT2] = "VP2"  # adds the viewport suffix, technically it's not a renderer shader suffix

RENDERER_PLUGIN = {REDSHIFT: "redshift4maya",
                   RENDERMAN: "RenderMan_for_Maya",
                   ARNOLD: "mtoa"}
