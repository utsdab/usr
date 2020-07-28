import os
import sys

from maya import cmds


def zooSetup():
    """Loads the zootools main maya plugins.
    """
    rootPythonPath = os.path.join(os.getenv("ZOOTOOLS_PRO_ROOT", ""), "python")
    rootPythonPath = os.path.abspath(rootPythonPath)

    if rootPythonPath is None:
        msg = """Zootools is missing the 'ZOOTOOLS_PRO_ROOT' environment variable
            in the maya mod file.
            """
        raise ValueError(msg)
    elif not os.path.exists(rootPythonPath):
        raise ValueError("Failed to find valid zootools python folder, incorrect .mod state")
    if rootPythonPath not in sys.path:
        sys.path.append(rootPythonPath)
    cmds.loadPlugin("zootools.py")


if __name__ == "__main__":
    cmds.evalDeferred(zooSetup)
