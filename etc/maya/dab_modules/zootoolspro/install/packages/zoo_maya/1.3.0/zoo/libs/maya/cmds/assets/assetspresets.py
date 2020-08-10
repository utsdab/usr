"""Sets the Default Directories for the assetPresets.json

"""

import json
import os
from zoo.libs.maya.cmds.assets.assetsimportexport import FILEQUICKDIRKEY

PRESETS = {FILEQUICKDIRKEY: ""}

jsonFilePath = os.path.join(os.path.dirname(__file__), 'lightpresets.json')
with open(jsonFilePath, 'w') as outfile:
    json.dump(PRESETS, outfile, sort_keys=True, indent=4, ensure_ascii=False)

