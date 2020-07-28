# Renderer nice names
ARNOLD = "Arnold"
RENDERMAN = "Renderman"
REDSHIFT = "Redshift"
# Render shader suffix
SHADER_SUFFIX_DICT = {REDSHIFT: "RS",
                      ARNOLD: "ARN",
                      RENDERMAN: "PXR"}

# Displacement Dictionary keys for attributes and values
DISP_ATTR_TYPE = "type"
DISP_ATTR_DIVISIONS = "divisions"
DISP_ATTR_SCALE = "scale"
DISP_ATTR_AUTOBUMP = "autoBump"
DISP_ATTR_IMAGEPATH = "imagePath"
DISP_ATTR_BOUNDS = "bounds"
DISP_ATTR_RENDERER = "zooRenderer"

# Displacement Network globals, network names and attributes
NW_DISPLACE_NODE = "zooDisplacementNetwork"
NW_DISPLACE_MESH_ATTR = "zooDisplaceMeshConnect"
NW_DISPLACE_SG_ATTR = "zooDisplaceSGConnect"
NW_DISPLACE_FILE_ATTR = "zooDisplaceFileConnect"
NW_DISPLACE_PLACE2D_ATTR = "zooDisplacePlace2dConnect"
NW_DISPLACE_NODE_ATTR = "zooDisplaceNode"

NW_ATTR_LIST = [NW_DISPLACE_MESH_ATTR, NW_DISPLACE_SG_ATTR, NW_DISPLACE_FILE_ATTR, NW_DISPLACE_PLACE2D_ATTR,
                NW_DISPLACE_NODE_ATTR]
