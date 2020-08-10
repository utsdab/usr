name = "zootoolspro"
version = "2.0.0"

tools = [
    "zoo_cmd"
]
requires = [
    "python"
]


def commands():
    global env
    env.PATH.append("{root}/install/core/bin")
    env.MAYA_MODULE_PATH.append("{root}/install/core/extensions/maya")
