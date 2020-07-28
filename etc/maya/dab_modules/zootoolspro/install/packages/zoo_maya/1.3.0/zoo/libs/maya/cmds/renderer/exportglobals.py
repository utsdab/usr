GENERICVERSIONNO = "1.0.0"  # the version number of the generic file format

ZOOSCENESUFFIX = "zooScene"

VERSIONKEY = "version"  # the key (name) of the version component of a generic dict
LIGHTS = "lightDict"  # the key (name) of the light component of a generic dict
SHADERS = "shaderDict"  # the key (name) of the shader component of a generic dict
MESHOBJECTS = "meshObjects"  # the key (name) of the mesh object dict

AREALIGHTS = "areaLights"
IBLSKYDOMES = "iblSkydomes"
DIRECTIONALS = "directionalLights"

NAMESPACELIST = "namespaces"  # the key for recording all namespaces in the scene

SMOOTHLEVEL = "smoothLevel"  # SubD attribute and dict key
DISPLAYSMOOTHMESH = "displaySmoothMesh"  # SubD attribute and dict key
USESMOOTHPREVIEWFORRENDERER = "useSmoothPreviewForRender"  # SubD attribute and dict key
RENDERSMOOTHLEVEL = "renderSmoothLevel"  # SubD attribute and dict key

REDSHIFT = "Redshift"
RENDERMAN = "Renderman"
ARNOLD = "Arnold"
GENERIC = "Generic"

SUPPORTEDRENDERERLIST = [REDSHIFT, RENDERMAN, ARNOLD]

LOCGRPNAME = "lightMatchLocs_grp"
LIGHTGRPNAME = "Lights_grp"

# ZOO ABC ATTRIBUTES for alembic
ZOOABC_MESH = "zooABC_mesh"
ZOOABC_LIGHT = "zooABC_light"
ZOOABC_CAM = "zooABC_camera"
ZOOABC_LOC = "zooABC_locator"
ZOOABC_CURVE = "zooABC_curve"
ZOOABC_PREFIX = "zooABC"

RENDERMANAREALIGHTTYPES = ("PxrRectLight", "PxrSphereLight", "PxrDiskLight")

RENDERERAREALIGHTS = {REDSHIFT: "RedshiftPhysicalLight",
                      RENDERMAN: RENDERMANAREALIGHTTYPES,
                      ARNOLD: "aiAreaLight"}

RENDERERDIRECTIONALLIGHTS = {REDSHIFT: "directionalLight",
                             RENDERMAN: "PxrDistantLight",
                             ARNOLD: "directionalLight"}

RENDERERSKYDOMELIGHTS = {REDSHIFT: "RedshiftDomeLight",
                         RENDERMAN: "PxrDomeLight",
                         ARNOLD: "aiSkyDomeLight"}

THUMBNAIL = "thumbnail"