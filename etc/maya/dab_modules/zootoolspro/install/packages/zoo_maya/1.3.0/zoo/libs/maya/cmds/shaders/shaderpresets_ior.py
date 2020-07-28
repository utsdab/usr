"""Sets the Default Presets for the shaderpresets_ior.json

"""

import json
import os

DIFFUSE = 'gDiffuseColor_srgb'
DIFFUSEWEIGHT = 'gDiffuseWeight'
SPECWEIGHT = 'gSpecWeight'
SPECCOLOR = 'gSpecColor_srgb'
SPECROUGHNESS = 'gSpecRoughness'
SPECIOR = 'gSpecIor'
COATCOLOR = 'gCoatColor_srgb'
COATWEIGHT = 'gCoatWeight'
COATROUGHNESS = 'gCoatRoughness'
COATIOR = 'gCoatIor'

SHADERPRESETS = {}

SHADERPRESETS["Matte Grey"] = {DIFFUSE: (.5, .5, .5),
                               DIFFUSEWEIGHT: 1.0,
                               SPECWEIGHT: 0.0,
                               SPECCOLOR: (1.0, 1.0, 1.0),
                               SPECROUGHNESS: 0.0,
                               SPECIOR: 1.5,
                               COATCOLOR: (1.0, 1.0, 1.0),
                               COATWEIGHT: 0.0,
                               COATROUGHNESS: 0.0,
                               COATIOR: 1.5}

SHADERPRESETS["Gold"] = {DIFFUSE: (0.0, 0.0, 0.0),
                               DIFFUSEWEIGHT: 1.0,
                               SPECWEIGHT: 1.0,
                               SPECCOLOR: (0.939, 0.761, 0.340),
                               SPECROUGHNESS: 0.1,
                               SPECIOR: 20.0,
                               COATCOLOR: (1.0, 1.0, 1.0),
                               COATWEIGHT: 0,
                               COATROUGHNESS: .2,
                               COATIOR: 1.5}

SHADERPRESETS["Car Paint Red"] = {DIFFUSE: (0.0, 0.0, 0.0),
                               DIFFUSEWEIGHT: 1.0,
                               SPECWEIGHT: 1.0,
                               SPECCOLOR: (1.0, 0.0, 0.0),
                               SPECROUGHNESS: 0.5,
                               SPECIOR: 20.0,
                               COATCOLOR: (1.0, 1.0, 1.0),
                               COATWEIGHT: 1,
                               COATROUGHNESS: .1,
                               COATIOR: 1.5}

SHADERPRESETS["Car Paint Purple"] = {DIFFUSE: (0.0, 0.0, 0.0),
                               DIFFUSEWEIGHT: 1.0,
                               SPECWEIGHT: 1.0,
                               SPECCOLOR: (0.608, 0.217, 1.000),
                               SPECROUGHNESS: 0.5,
                               SPECIOR: 20.0,
                               COATCOLOR: (1.0, 1.0, 1.0),
                               COATWEIGHT: 1,
                               COATROUGHNESS: .1,
                               COATIOR: 1.5}

SHADERPRESETS["Chrome"] = {DIFFUSE: (0.0, 0.0, 0.0),
                               DIFFUSEWEIGHT: 1.0,
                               SPECWEIGHT: 1.0,
                               SPECCOLOR: (1.0, 1.0, 1.0),
                               SPECROUGHNESS: 0.1,
                               SPECIOR: 20.0,
                               COATCOLOR: (1.0, 1.0, 1.0),
                               COATWEIGHT: 0.0,
                               COATROUGHNESS: 0.0,
                               COATIOR: 1.5}

SHADERPRESETS["Chrome Rough"] = {DIFFUSE: (0.0, 0.0, 0.0),
                               DIFFUSEWEIGHT: 1.0,
                               SPECWEIGHT: 1.0,
                               SPECCOLOR: (1.0, 1.0, 1.0),
                               SPECROUGHNESS: 0.4,
                               SPECIOR: 20.0,
                               COATCOLOR: (1.0, 1.0, 1.0),
                               COATWEIGHT: 0.0,
                               COATROUGHNESS: 0.0,
                               COATIOR: 1.5}

SHADERPRESETS["Metal Dull"] = {DIFFUSE: (0.0, 0.0, 0.0),
                               DIFFUSEWEIGHT: 1.0,
                               SPECWEIGHT: 1.0,
                               SPECCOLOR: (0.5, 0.5, 0.5),
                               SPECROUGHNESS: .45,
                               SPECIOR: 4.0,
                               COATCOLOR: (1.0, 1.0, 1.0),
                               COATWEIGHT: 0.0,
                               COATROUGHNESS: 0.0,
                               COATIOR: 1.5}

SHADERPRESETS["Metal Dull Polish"] = {DIFFUSE: (0.0, 0.0, 0.0),
                               DIFFUSEWEIGHT: 1.0,
                               SPECWEIGHT: 1.0,
                               SPECCOLOR: (0.5, 0.5, 0.5),
                               SPECROUGHNESS: .45,
                               SPECIOR: 4.0,
                               COATCOLOR: (1.0, 1.0, 1.0),
                               COATWEIGHT: 1,
                               COATROUGHNESS: 0.2,
                               COATIOR: 1.5}


SHADERPRESETS["Copper"] = {DIFFUSE: (0.0, 0.0, 0.0),
                               DIFFUSEWEIGHT: 1.0,
                               SPECWEIGHT: 1.0,
                               SPECCOLOR: (0.755, 0.5, 0.156),
                               SPECROUGHNESS: 0.4,
                               SPECIOR: 4.0,
                               COATCOLOR: (1.0, 1.0, 1.0),
                               COATWEIGHT: 0.0,
                               COATROUGHNESS: 0.0,
                               COATIOR: 1.5}

SHADERPRESETS["Plastic Shiny White"] = {DIFFUSE: (0.9, 0.9, 0.9),
                               DIFFUSEWEIGHT: 1.0,
                               SPECWEIGHT: 1.0,
                               SPECCOLOR: (1.0, 1.0, 1.0),
                               SPECROUGHNESS: 0.1,
                               SPECIOR: 1.5,
                               COATCOLOR: (1.0, 1.0, 1.0),
                               COATWEIGHT: 0.0,
                               COATROUGHNESS: 0.0,
                               COATIOR: 1.5}

SHADERPRESETS["Plastic Shiny Red"] = {DIFFUSE: (1.0, 0.0, 0.0),
                               DIFFUSEWEIGHT: 1.0,
                               SPECWEIGHT: 1.0,
                               SPECCOLOR: (1.0, 1.0, 1.0),
                               SPECROUGHNESS: 0.1,
                               SPECIOR: 1.5,
                               COATCOLOR: (1.0, 1.0, 1.0),
                               COATWEIGHT: 0.0,
                               COATROUGHNESS: 0.0,
                               COATIOR: 1.5}

SHADERPRESETS["Plastic Shiny Black"] = {DIFFUSE: (0.05, 0.05, 0.05),
                               DIFFUSEWEIGHT: 1.0,
                               SPECWEIGHT: 1.0,
                               SPECCOLOR: (1.0, 1.0, 1.0),
                               SPECROUGHNESS: 0.1,
                               SPECIOR: 1.5,
                               COATCOLOR: (1.0, 1.0, 1.0),
                               COATWEIGHT: 0.0,
                               COATROUGHNESS: 0.0,
                               COATIOR: 1.5}

SHADERPRESETS["Plastic Mid Black"] = {DIFFUSE: (0.05, 0.05, 0.05),
                               DIFFUSEWEIGHT: 1.0,
                               SPECWEIGHT: 1.0,
                               SPECCOLOR: (1.0, 1.0, 1.0),
                               SPECROUGHNESS: 0.5,
                               SPECIOR: 1.5,
                               COATCOLOR: (1.0, 1.0, 1.0),
                               COATWEIGHT: 0.5,
                               COATROUGHNESS: 0.3,
                               COATIOR: 1.3}

SHADERPRESETS["Plastic Rough White"] = {DIFFUSE: (0.9, 0.9, 0.9),
                               DIFFUSEWEIGHT: 1.0,
                               SPECWEIGHT: 1.0,
                               SPECCOLOR: (1.0, 1.0, 1.0),
                               SPECROUGHNESS: 0.5,
                               SPECIOR: 1.5,
                               COATCOLOR: (1.0, 1.0, 1.0),
                               COATWEIGHT: 0.0,
                               COATROUGHNESS: 0.0,
                               COATIOR: 1.5}

SHADERPRESETS["Plastic Rough Red"] = {DIFFUSE: (1.0, 0.0, 0.0),
                               DIFFUSEWEIGHT: 1.0,
                               SPECWEIGHT: 1.0,
                               SPECCOLOR: (1.0, 1.0, 1.0),
                               SPECROUGHNESS: 0.5,
                               SPECIOR: 1.5,
                               COATCOLOR: (1.0, 1.0, 1.0),
                               COATWEIGHT: 0.0,
                               COATROUGHNESS: 0.0,
                               COATIOR: 1.5}

SHADERPRESETS["Plastic Mid Red"] = {DIFFUSE: (1.0, 0.0, 0.0),
                               DIFFUSEWEIGHT: 1.0,
                               SPECWEIGHT: 1.0,
                               SPECCOLOR: (1.0, 1.0, 1.0),
                               SPECROUGHNESS: 0.5,
                               SPECIOR: 1.5,
                               COATCOLOR: (1.0, 1.0, 1.0),
                               COATWEIGHT: 0.5,
                               COATROUGHNESS: 0.3,
                               COATIOR: 1.3}

SHADERPRESETS["Plastic Rough Black"] = {DIFFUSE: (0.05, 0.05, 0.05),
                               DIFFUSEWEIGHT: 1.0,
                               SPECWEIGHT: 1.0,
                               SPECCOLOR: (1.0, 1.0, 1.0),
                               SPECROUGHNESS: 0.5,
                               SPECIOR: 1.5,
                               COATCOLOR: (1.0, 1.0, 1.0),
                               COATWEIGHT: 0.0,
                               COATROUGHNESS: 0.3,
                               COATIOR: 1.5}

SHADERPRESETS["Backlit Green"] = {DIFFUSE: (.0, 0.667, .0),
                               DIFFUSEWEIGHT: 1.0,
                               SPECWEIGHT: 0.5,
                               SPECCOLOR: (0.694, 1.0, 0.981),
                               SPECROUGHNESS: 0.7,
                               SPECIOR: 4,
                               COATCOLOR: (1.0, 1.0, 1.0),
                               COATWEIGHT: 1.0,
                               COATROUGHNESS: 0.5,
                               COATIOR: 1.3}

SHADERPRESETS["Backlit Skin"] = {DIFFUSE: (0.760, 0.560, 0.456),
                               DIFFUSEWEIGHT: 1.0,
                               SPECWEIGHT: 0.5,
                               SPECCOLOR: (0.867, 1.0, 0.991),
                               SPECROUGHNESS: 0.7,
                               SPECIOR: 4,
                               COATCOLOR: (1.0, 1.0, 1.0),
                               COATWEIGHT: 1.0,
                               COATROUGHNESS: 0.5,
                               COATIOR: 1.3}

jsonFilePath = os.path.join(os.path.dirname(__file__), 'shaderpresets_ior.json')
with open(jsonFilePath, 'w') as outfile:
    json.dump(SHADERPRESETS, outfile, sort_keys=True, indent=4, ensure_ascii=False)

