ZOO_SK_NCLOTH_NETWORK = "zooSkNClothNetwork"

# Skinned NCloth Nodes
ORIGINAL_MESH_TFRM = "originalMeshTransform"
POLYSMOOTH_MESH_TFRM = "polySmoothMeshTransform"
CLOTH_MESH_TFRM = "clothMeshTransform"
CLOTH_MESH_SHAPE = "clothMeshShape"
BLENDER_MESH_TFRM = "blenderMeshTransform"
BLENDSHAPE_ORIG_NODE = "blendshapeOrigNode"
BLENDSHAPE_CLOTH_NODE = "blendshapeClothNode"
NCLOTH_NODE = "nClothNode"
NCLOTH_TRANSFORM = "nClothTransform"
NUCLEUS_NODE = "nucleusNode"
CLOTH_NODES_GRP = "clothNodesGrp"

SK_NCLOTH_NODE_DICT = {ORIGINAL_MESH_TFRM: "",
                       POLYSMOOTH_MESH_TFRM: "",
                       CLOTH_MESH_TFRM: "",
                       CLOTH_MESH_SHAPE: "",
                       BLENDER_MESH_TFRM: "",
                       BLENDSHAPE_ORIG_NODE: "",
                       BLENDSHAPE_CLOTH_NODE: "",
                       NCLOTH_NODE: "",
                       NCLOTH_TRANSFORM: "",
                       NUCLEUS_NODE: "",
                       CLOTH_NODES_GRP: ""}

# NCloth Blend Attribute Name
NCA_BLEND_ATTR = "nCloth"
# NCloth Attributes
NCA_INPUT_ATTRACT = 'inputMeshAttract'
NCA_LIFT = 'lift'
# TShirt Settings for nCloth
NCA_THICKNESS = 'thickness'
NCA_STRETCH_RESISTANCE = 'stretchResistance'
NCA_COMPRESSION_RESISTANCE = 'compressionResistance'
NCA_BEND_RESISTANCE = 'bendResistance'
NCA_BEND_ANGLE_DROPOFF = 'bendAngleDropoff'
NCA_SHEAR_RESISTANCE = 'shearResistance'
NCA_POINT_MASS = 'pointMass'
NCA_TANGENTIAL_DRAG = 'tangentialDrag'
NCA_DAMP = 'damp'
NCA_SCALING_RELATION = 'scalingRelation'
NCA_PUSH_OUT_RADIUS = 'pushOutRadius'
# Other
NCA_LOCAL_SPACE_OUTPUT = 'localSpaceOutput'
NCA_SELF_COLLIDE_WIDTH_SCALE = 'selfCollideWidthScale'
# Nucleus
NCA_NUCLEUS_STARTFRAME = "startFrame"
NCA_NUCLEUS_SUBSTEPS = "subSteps"
NCA_NUCLEUS_MAX_COLLISIONS = "maxCollisionIterations"
NCA_NUCLEUS_SPACESCALE = "spaceScale"
NCA_NUCLEUS_GRAVITY = "gravity"
# GUI Network Node attr
NCA_NETWORK_SUBD_DIVISIONS = "subDDivisions"
NCA_NETWORK_PRESET_INDEX = "presetIndex"

SKINNED_NCLOTH_ATTRS = [NCA_INPUT_ATTRACT, NCA_LIFT, NCA_THICKNESS, NCA_STRETCH_RESISTANCE,
                        NCA_COMPRESSION_RESISTANCE, NCA_BEND_RESISTANCE, NCA_BEND_ANGLE_DROPOFF, NCA_SHEAR_RESISTANCE,
                        NCA_POINT_MASS, NCA_TANGENTIAL_DRAG, NCA_DAMP, NCA_SCALING_RELATION, NCA_LOCAL_SPACE_OUTPUT,
                        NCA_SELF_COLLIDE_WIDTH_SCALE]
BLEND_NCLOTH_ATTRS = [NCA_BLEND_ATTR]
NUCLEUS_NCLOTH_ATTRS = [NCA_NUCLEUS_STARTFRAME, NCA_NUCLEUS_SUBSTEPS, NCA_NUCLEUS_MAX_COLLISIONS,
                        NCA_NUCLEUS_SPACESCALE, NCA_NUCLEUS_GRAVITY]

# -----------------------------
# NUCLEUS DICTIONARY VALUES
# -----------------------------

NUCLEUS_DEFAULT_PRESET = {NCA_NUCLEUS_STARTFRAME: 1.0,
                          NCA_NUCLEUS_SUBSTEPS: 3.0,
                          NCA_NUCLEUS_MAX_COLLISIONS: 4.0,
                          NCA_NUCLEUS_SPACESCALE: 0.01,
                          NCA_NUCLEUS_GRAVITY: 0.0
                          }

# -----------------------------
# SKINNED NCLOTH PRESETS
#  -----------------------------

# T-Shirt is the default preset
TSHIRT_PRESET_DICT = {NCA_INPUT_ATTRACT: 1.0,
                      NCA_LIFT: 0.0001,
                      NCA_STRETCH_RESISTANCE: 35.0,
                      NCA_COMPRESSION_RESISTANCE: 10.0,
                      NCA_BEND_RESISTANCE: 0.4,
                      NCA_BEND_ANGLE_DROPOFF: 0.4,
                      NCA_SHEAR_RESISTANCE: 0.0,
                      NCA_POINT_MASS: 0.6,
                      NCA_TANGENTIAL_DRAG: 0.1,
                      NCA_DAMP: 0.8,
                      NCA_SCALING_RELATION: 1.0,
                      NCA_PUSH_OUT_RADIUS: 10.0,
                      NCA_THICKNESS: 0.005,
                      NCA_LOCAL_SPACE_OUTPUT: 1.0,
                      NCA_SELF_COLLIDE_WIDTH_SCALE: 1
                      }

AIRBAG_PRESET_DICT = {NCA_INPUT_ATTRACT: 1.0,
                      NCA_LIFT: 0.05,
                      NCA_STRETCH_RESISTANCE: 40.0,
                      NCA_COMPRESSION_RESISTANCE: 10.0,
                      NCA_BEND_RESISTANCE: 1.0,
                      NCA_BEND_ANGLE_DROPOFF: 0.297,
                      NCA_SHEAR_RESISTANCE: 0.0,
                      NCA_POINT_MASS: 0.5,
                      NCA_TANGENTIAL_DRAG: 0.1,
                      NCA_DAMP: 0.0,
                      NCA_SCALING_RELATION: 1.0,
                      NCA_PUSH_OUT_RADIUS: 10.0,
                      NCA_THICKNESS: 0.005,
                      NCA_LOCAL_SPACE_OUTPUT: 1.0,
                      NCA_SELF_COLLIDE_WIDTH_SCALE: 1.071
                      }

BEACHBALL_PRESET_DICT = {NCA_INPUT_ATTRACT: 1.0,
                         NCA_LIFT: 0.05,
                         NCA_STRETCH_RESISTANCE: 60.0,
                         NCA_COMPRESSION_RESISTANCE: 30.0,
                         NCA_BEND_RESISTANCE: 1.0,
                         NCA_BEND_ANGLE_DROPOFF: 0.298,
                         NCA_SHEAR_RESISTANCE: 0.0,
                         NCA_POINT_MASS: 0.3,
                         NCA_TANGENTIAL_DRAG: 0.1,
                         NCA_DAMP: 0.0,
                         NCA_SCALING_RELATION: 1.0,
                         NCA_PUSH_OUT_RADIUS: 10.0,
                         NCA_THICKNESS: 0.005,
                         NCA_LOCAL_SPACE_OUTPUT: 1.0,
                         NCA_SELF_COLLIDE_WIDTH_SCALE: 1.071,
                         }

BURLAP_PRESET_DICT = {NCA_INPUT_ATTRACT: 1.0,
                      NCA_LIFT: 0.05,
                      NCA_STRETCH_RESISTANCE: 40.0,
                      NCA_COMPRESSION_RESISTANCE: 40.0,
                      NCA_BEND_RESISTANCE: 3.0,
                      NCA_BEND_ANGLE_DROPOFF: 0.603,
                      NCA_SHEAR_RESISTANCE: 0.0,
                      NCA_POINT_MASS: 1.5,
                      NCA_TANGENTIAL_DRAG: 0.4,
                      NCA_DAMP: 4.0,
                      NCA_SCALING_RELATION: 1.0,
                      NCA_PUSH_OUT_RADIUS: 10.0,
                      NCA_THICKNESS: 0.005,
                      NCA_LOCAL_SPACE_OUTPUT: 1.0,
                      NCA_SELF_COLLIDE_WIDTH_SCALE: 1.071,
                      }

CHAINMAIL_PRESET_DICT = {NCA_INPUT_ATTRACT: 1.0,
                         NCA_LIFT: 0.05,
                         NCA_STRETCH_RESISTANCE: 50.0,
                         NCA_COMPRESSION_RESISTANCE: 2.0,
                         NCA_BEND_RESISTANCE: 0.01,
                         NCA_BEND_ANGLE_DROPOFF: 0.818,
                         NCA_SHEAR_RESISTANCE: 0.0,
                         NCA_POINT_MASS: 10.0,
                         NCA_TANGENTIAL_DRAG: 0.2,
                         NCA_DAMP: 0.05,
                         NCA_SCALING_RELATION: 1.0,
                         NCA_PUSH_OUT_RADIUS: 10.0,
                         NCA_THICKNESS: 0.005,
                         NCA_LOCAL_SPACE_OUTPUT: 1.0,
                         NCA_SELF_COLLIDE_WIDTH_SCALE: 1.071,
                         }

CHIFFON_PRESET_DICT = {NCA_INPUT_ATTRACT: 1.0,
                       NCA_LIFT: 0.05,
                       NCA_STRETCH_RESISTANCE: 40.0,
                       NCA_COMPRESSION_RESISTANCE: 20.0,
                       NCA_BEND_RESISTANCE: 0.2,
                       NCA_BEND_ANGLE_DROPOFF: 0.6,
                       NCA_SHEAR_RESISTANCE: 0.0,
                       NCA_POINT_MASS: 0.15,
                       NCA_TANGENTIAL_DRAG: 0.4,
                       NCA_DAMP: 2.0,
                       NCA_SCALING_RELATION: 1.0,
                       NCA_PUSH_OUT_RADIUS: 10.0,
                       NCA_THICKNESS: 0.005,
                       NCA_LOCAL_SPACE_OUTPUT: 1.0,
                       NCA_SELF_COLLIDE_WIDTH_SCALE: 1.071,
                       }

CONCRETE_PRESET_DICT = {NCA_INPUT_ATTRACT: 1.0,
                        NCA_LIFT: 0.05,
                        NCA_STRETCH_RESISTANCE: 20.0,
                        NCA_COMPRESSION_RESISTANCE: 20.0,
                        NCA_BEND_RESISTANCE: 0.0,
                        NCA_BEND_ANGLE_DROPOFF: 0.0,
                        NCA_SHEAR_RESISTANCE: 0.0,
                        NCA_POINT_MASS: 20.0,
                        NCA_TANGENTIAL_DRAG: 0.0,
                        NCA_DAMP: 1.0,
                        NCA_SCALING_RELATION: 1.0,
                        NCA_PUSH_OUT_RADIUS: 10.0,
                        NCA_THICKNESS: 0.005,
                        NCA_LOCAL_SPACE_OUTPUT: 1.0,
                        NCA_SELF_COLLIDE_WIDTH_SCALE: 1.071,
                        }

HEAVYDENIM_PRESET_DICT = {NCA_INPUT_ATTRACT: 1.0,
                          NCA_LIFT: 0.05,
                          NCA_STRETCH_RESISTANCE: 50.0,
                          NCA_COMPRESSION_RESISTANCE: 20.0,
                          NCA_BEND_RESISTANCE: 0.4,
                          NCA_BEND_ANGLE_DROPOFF: 0.603,
                          NCA_SHEAR_RESISTANCE: 0.0,
                          NCA_POINT_MASS: 2.0,
                          NCA_TANGENTIAL_DRAG: 0.1,
                          NCA_DAMP: 0.8,
                          NCA_SCALING_RELATION: 1.0,
                          NCA_PUSH_OUT_RADIUS: 10.0,
                          NCA_THICKNESS: 1.0,
                          NCA_LOCAL_SPACE_OUTPUT: 1.0,
                          NCA_SELF_COLLIDE_WIDTH_SCALE: 1.0,
                          }

HONEY_PRESET_DICT = {NCA_INPUT_ATTRACT: 1.0,
                     NCA_LIFT: 0.05,
                     NCA_STRETCH_RESISTANCE: 0.01,
                     NCA_COMPRESSION_RESISTANCE: 0.01,
                     NCA_BEND_RESISTANCE: 0.7,
                     NCA_BEND_ANGLE_DROPOFF: 0.851,
                     NCA_SHEAR_RESISTANCE: 0.0,
                     NCA_POINT_MASS: 10.0,
                     NCA_TANGENTIAL_DRAG: 0.0,
                     NCA_DAMP: 1.5,
                     NCA_SCALING_RELATION: 1.0,
                     NCA_PUSH_OUT_RADIUS: 10.0,
                     NCA_THICKNESS: 1.0,
                     NCA_LOCAL_SPACE_OUTPUT: 1.0,
                     NCA_SELF_COLLIDE_WIDTH_SCALE: 1.0,
                     }

LAVA_PRESET_DICT = {NCA_INPUT_ATTRACT: 1.0,
                    NCA_LIFT: 0.05,
                    NCA_STRETCH_RESISTANCE: 0.01,
                    NCA_COMPRESSION_RESISTANCE: 0.01,
                    NCA_BEND_RESISTANCE: 0.7,
                    NCA_BEND_ANGLE_DROPOFF: 0.851,
                    NCA_SHEAR_RESISTANCE: 0.0,
                    NCA_POINT_MASS: 10.0,
                    NCA_TANGENTIAL_DRAG: 0.0,
                    NCA_DAMP: 1.5,
                    NCA_SCALING_RELATION: 1.0,
                    NCA_PUSH_OUT_RADIUS: 10.0,
                    NCA_THICKNESS: 1.0,
                    NCA_LOCAL_SPACE_OUTPUT: 1.0,
                    NCA_SELF_COLLIDE_WIDTH_SCALE: 1.0,
                    }

LOOSETHICKKNIT_PRESET_DICT = {NCA_INPUT_ATTRACT: 1.0,
                              NCA_LIFT: 0.05,
                              NCA_STRETCH_RESISTANCE: 30.0,
                              NCA_COMPRESSION_RESISTANCE: 5.0,
                              NCA_BEND_RESISTANCE: 0.5,
                              NCA_BEND_ANGLE_DROPOFF: 0.603,
                              NCA_SHEAR_RESISTANCE: 0.0,
                              NCA_POINT_MASS: 0.8,
                              NCA_TANGENTIAL_DRAG: 0.4,
                              NCA_DAMP: 1.0,
                              NCA_SCALING_RELATION: 1.0,
                              NCA_PUSH_OUT_RADIUS: 10.0,
                              NCA_THICKNESS: 1.0,
                              NCA_LOCAL_SPACE_OUTPUT: 1.0,
                              NCA_SELF_COLLIDE_WIDTH_SCALE: 1.0,
                              }

PLASTICSHELL_PRESET_DICT = {NCA_INPUT_ATTRACT: 1.0,
                            NCA_LIFT: 0.05,
                            NCA_STRETCH_RESISTANCE: 20.0,
                            NCA_COMPRESSION_RESISTANCE: 20.0,
                            NCA_BEND_RESISTANCE: 20.0,
                            NCA_BEND_ANGLE_DROPOFF: 0.0,
                            NCA_SHEAR_RESISTANCE: 0.0,
                            NCA_POINT_MASS: 2.0,
                            NCA_TANGENTIAL_DRAG: 0.0,
                            NCA_DAMP: 1.0,
                            NCA_SCALING_RELATION: 1.0,
                            NCA_PUSH_OUT_RADIUS: 10.0,
                            NCA_THICKNESS: 1.0,
                            NCA_LOCAL_SPACE_OUTPUT: 1.0,
                            NCA_SELF_COLLIDE_WIDTH_SCALE: 1.0,
                            }

PUTTY_PRESET_DICT = {NCA_INPUT_ATTRACT: 1.0,
                     NCA_LIFT: 0.05,
                     NCA_STRETCH_RESISTANCE: 5.0,
                     NCA_COMPRESSION_RESISTANCE: 3.0,
                     NCA_BEND_RESISTANCE: 3.0,
                     NCA_BEND_ANGLE_DROPOFF: 0.0,
                     NCA_SHEAR_RESISTANCE: 0.0,
                     NCA_POINT_MASS: 10.0,
                     NCA_TANGENTIAL_DRAG: 0.0,
                     NCA_DAMP: 1.0,
                     NCA_SCALING_RELATION: 1.0,
                     NCA_PUSH_OUT_RADIUS: 10.0,
                     NCA_THICKNESS: 1.0,
                     NCA_LOCAL_SPACE_OUTPUT: 1.0,
                     NCA_SELF_COLLIDE_WIDTH_SCALE: 1.0,
                     }

RUBBERSHEET_PRESET_DICT = {NCA_INPUT_ATTRACT: 1.0,
                           NCA_LIFT: 0.05,
                           NCA_STRETCH_RESISTANCE: 4.0,
                           NCA_COMPRESSION_RESISTANCE: 2.0,
                           NCA_BEND_RESISTANCE: 0.1,
                           NCA_BEND_ANGLE_DROPOFF: 0.603,
                           NCA_SHEAR_RESISTANCE: 0.0,
                           NCA_POINT_MASS: 2.0,
                           NCA_TANGENTIAL_DRAG: 0.05,
                           NCA_DAMP: 0.01,
                           NCA_SCALING_RELATION: 1.0,
                           NCA_PUSH_OUT_RADIUS: 10.0,
                           NCA_THICKNESS: 1.0,
                           NCA_LOCAL_SPACE_OUTPUT: 1.0,
                           NCA_SELF_COLLIDE_WIDTH_SCALE: 1.0,
                           }

SILK_PRESET_DICT = {NCA_INPUT_ATTRACT: 1.0,
                    NCA_LIFT: 0.05,
                    NCA_STRETCH_RESISTANCE: 60.0,
                    NCA_COMPRESSION_RESISTANCE: 10.0,
                    NCA_BEND_RESISTANCE: 0.05,
                    NCA_BEND_ANGLE_DROPOFF: 0.3,
                    NCA_SHEAR_RESISTANCE: 0.0,
                    NCA_POINT_MASS: 0.2,
                    NCA_TANGENTIAL_DRAG: 0.05,
                    NCA_DAMP: 0.2,
                    NCA_SCALING_RELATION: 1.0,
                    NCA_PUSH_OUT_RADIUS: 10.0,
                    NCA_THICKNESS: 1.0,
                    NCA_LOCAL_SPACE_OUTPUT: 1.0,
                    NCA_SELF_COLLIDE_WIDTH_SCALE: 1.0,
                    }

SOFTSHEETMETAL_PRESET_DICT = {NCA_INPUT_ATTRACT: 1.0,
                              NCA_LIFT: 0.05,
                              NCA_STRETCH_RESISTANCE: 100.0,
                              NCA_COMPRESSION_RESISTANCE: 100.0,
                              NCA_BEND_RESISTANCE: 100.0,
                              NCA_BEND_ANGLE_DROPOFF: 0.0,
                              NCA_SHEAR_RESISTANCE: 0.0,
                              NCA_POINT_MASS: 20.0,
                              NCA_TANGENTIAL_DRAG: 0.0,
                              NCA_DAMP: 1.0,
                              NCA_SCALING_RELATION: 1.0,
                              NCA_PUSH_OUT_RADIUS: 10.0,
                              NCA_THICKNESS: 1.0,
                              NCA_LOCAL_SPACE_OUTPUT: 1.0,
                              NCA_SELF_COLLIDE_WIDTH_SCALE: 1.0,
                              }

SOLIDRUBBER_PRESET_DICT = {NCA_INPUT_ATTRACT: 1.0,
                           NCA_LIFT: 0.05,
                           NCA_STRETCH_RESISTANCE: 20.0,
                           NCA_COMPRESSION_RESISTANCE: 20.0,
                           NCA_BEND_RESISTANCE: 20.0,
                           NCA_BEND_ANGLE_DROPOFF: 0.0,
                           NCA_SHEAR_RESISTANCE: 0.0,
                           NCA_POINT_MASS: 2.0,
                           NCA_TANGENTIAL_DRAG: 0.0,
                           NCA_DAMP: 0.8,
                           NCA_SCALING_RELATION: 1.0,
                           NCA_PUSH_OUT_RADIUS: 10.0,
                           NCA_THICKNESS: 1.0,
                           NCA_LOCAL_SPACE_OUTPUT: 1.0,
                           NCA_SELF_COLLIDE_WIDTH_SCALE: 1.0,
                           }

THICKLEATHER_PRESET_DICT = {NCA_INPUT_ATTRACT: 1.0,
                            NCA_LIFT: 0.05,
                            NCA_STRETCH_RESISTANCE: 50.0,
                            NCA_COMPRESSION_RESISTANCE: 50.0,
                            NCA_BEND_RESISTANCE: 10.0,
                            NCA_BEND_ANGLE_DROPOFF: 0.727,
                            NCA_SHEAR_RESISTANCE: 0.0,
                            NCA_POINT_MASS: 3.0,
                            NCA_TANGENTIAL_DRAG: 0.2,
                            NCA_DAMP: 8.0,
                            NCA_SCALING_RELATION: 1.0,
                            NCA_PUSH_OUT_RADIUS: 10.0,
                            NCA_THICKNESS: 1.0,
                            NCA_LOCAL_SPACE_OUTPUT: 1.0,
                            NCA_SELF_COLLIDE_WIDTH_SCALE: 1.0,
                            }

WATERBALLOON_PRESET_DICT = {NCA_INPUT_ATTRACT: 1.0,
                            NCA_LIFT: 0.05,
                            NCA_STRETCH_RESISTANCE: 1.0,
                            NCA_COMPRESSION_RESISTANCE: 1.0,
                            NCA_BEND_RESISTANCE: 0.1,
                            NCA_BEND_ANGLE_DROPOFF: 0.504,
                            NCA_SHEAR_RESISTANCE: 0.0,
                            NCA_POINT_MASS: 10.0,
                            NCA_TANGENTIAL_DRAG: 0.0,
                            NCA_DAMP: 0.0,
                            NCA_SCALING_RELATION: 1.0,
                            NCA_PUSH_OUT_RADIUS: 10.0,
                            NCA_THICKNESS: 1.0,
                            NCA_LOCAL_SPACE_OUTPUT: 1.0,
                            NCA_SELF_COLLIDE_WIDTH_SCALE: 1.0,
                            }

WATERVOLUME_PRESET_DICT = {NCA_INPUT_ATTRACT: 1.0,
                           NCA_LIFT: 0.05,
                           NCA_STRETCH_RESISTANCE: 0.02,
                           NCA_COMPRESSION_RESISTANCE: 0.02,
                           NCA_BEND_RESISTANCE: 0.5,
                           NCA_BEND_ANGLE_DROPOFF: 0.3,
                           NCA_SHEAR_RESISTANCE: 0.0,
                           NCA_POINT_MASS: 10.0,
                           NCA_TANGENTIAL_DRAG: 0.0,
                           NCA_DAMP: 0.0,
                           NCA_SCALING_RELATION: 1.0,
                           NCA_PUSH_OUT_RADIUS: 10.0,
                           NCA_THICKNESS: 1.0,
                           NCA_LOCAL_SPACE_OUTPUT: 1.0,
                           NCA_SELF_COLLIDE_WIDTH_SCALE: 1.0,
                           }

# NCloth dict used with combo box presets
NCLOTH_SKINNED_PRESET_DICT = {"Air Bag": AIRBAG_PRESET_DICT,
                              "Beach Ball": BEACHBALL_PRESET_DICT,
                              "Burlap": BURLAP_PRESET_DICT,
                              "Chain Mail": CHAINMAIL_PRESET_DICT,
                              "Chiffon": CHIFFON_PRESET_DICT,
                              "Concrete": CONCRETE_PRESET_DICT,
                              "Heavy Denim": HEAVYDENIM_PRESET_DICT,
                              "Honey": HONEY_PRESET_DICT,
                              "Lava": LAVA_PRESET_DICT,
                              "Loose Thick Knit": LOOSETHICKKNIT_PRESET_DICT,
                              "Plastic Shell": PLASTICSHELL_PRESET_DICT,
                              "Putty": PUTTY_PRESET_DICT,
                              "Rubber Sheet": RUBBERSHEET_PRESET_DICT,
                              "Silk": SILK_PRESET_DICT,
                              "Soft Sheet Metal": SOFTSHEETMETAL_PRESET_DICT,
                              "Solid Rubber": SOLIDRUBBER_PRESET_DICT,
                              "Thick Leather": THICKLEATHER_PRESET_DICT,
                              "TShirt": TSHIRT_PRESET_DICT,
                              "Water Balloon": WATERBALLOON_PRESET_DICT,
                              "Water Volume": WATERVOLUME_PRESET_DICT
                              }

# Creates an alphabetized list of nCloth presets for the combo box.
NCLOTH_PRESET_NAME_LIST = list()
for name in NCLOTH_SKINNED_PRESET_DICT:
    NCLOTH_PRESET_NAME_LIST.append(name)
NCLOTH_PRESET_NAME_LIST.sort(key=str.lower)  # alphabetical
