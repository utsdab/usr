import getpass
import platform
import os
import sys


def isInMaya(executable=None):
    """Determines if the current running executable is maya.exe

    :return: True if running maya.exe
    :rtype: bool
    """
    executable = (executable or sys.executable).lower()
    endswithKey = ("maya", "maya.exe", "maya.bin")
    return os.path.basename(executable).endswith(endswithKey)


def isMayapy(executable=None):
    """Determines if the current running executable is mayapy.exe

    :return: True if running mayapy.exe
    :rtype: bool
    """
    executable = (executable or sys.executable).lower()
    endswithKey = ("mayapy", "mayapy.exe")
    return os.path.basename(executable).endswith(endswithKey)


def isMayaBatch(executable=None):
    """Determines if the current running executable is mayabatch.exe

    :return: True if running mayapy.exe
    :rtype: bool
    """
    executable = (executable or sys.executable).lower()
    endswithKey = ("mayabatch", "mayabatch.exe")
    return os.path.basename(executable).endswith(endswithKey)


def isIn3dsmax(executable=None):
    """Determines if the current running executable is 3dsmax.exe

    :return: True if running 3dsmax.exe
    :rtype: bool
    """
    executable = (executable or sys.executable).lower()
    endswithKey = ("3dsmax", "3dsmax.exe")
    return os.path.basename(executable).endswith(endswithKey)


def isInMotionBuilder(executable=None):
    """Determines if the current running executable is motionbuilder.exe

    :return: True if running motionbuilder.exe
    :rtype: bool
    """
    executable = (executable or sys.executable).lower()
    endswithKey = ("motionbuilder", "motionbuilder.exe")
    return os.path.basename(executable).endswith(endswithKey)


def isInHoudini(executable=None):
    """Determines if the current running executable is houdini.exe

    :return: True if running houdini.exe
    :rtype: bool
    """
    executable = (executable or sys.executable).lower()
    endswithKey = ("houdini", "houdinifx", "houdinicore", "happrentice")
    return os.path.basename(executable).startswith(endswithKey)


def isInBlender(executable=None):
    """Determines if the current running executable is blender

    :return: True if running houdini.exe
    :rtype: bool
    """
    executable = (executable or sys.executable).lower()
    endswithKey = ("blender", )
    return os.path.basename(executable).startswith(endswithKey)


def application():
    """Returns the currently running application

    :return: returns one of the following:
            maya
            3dsmax
            motionbuilder
            houdini
            standalone
    :rtype: str
    """
    if any((isInMaya(), isMayapy(), isMayaBatch())):
        return "maya"
    elif isIn3dsmax():
        return "3dsmax"
    elif isInMotionBuilder():
        return "motionbuilder"
    elif isInHoudini():
        return "houdini"
    # can extend this for other DCCs
    return "standalone"


def machineInfo():
    """Returns basic information about the current pc that this code is running on

    :return:
                {'OSRelease': '7',
                 'OSVersion': 'Windows-7-6.1.7601-SP1',
                 'executable': 'C:\\Program Files\\Autodesk\\Maya2018\\bin\\maya.exe',
                 'machineType': 'AMD64',
                 'node': 'COMPUTERNAME',
                 'processor': 'Intel64 Family 6 Model 44 Stepping 2, GenuineIntel',
                 'pythonVersion': '2.7.11 (default, Jul  1 2016, 02:08:48) [MSC v.1900 64 bit (AMD64)]',
                 'syspaths': list(str),
                 'env': dict(os.environ)
                 }
    :rtype: dict
    """
    machineDict = {"pythonVersion": sys.version,
                   "node": platform.node(),
                   "OSRelease": platform.release(),
                   "OSVersion": platform.platform(),
                   "processor": platform.processor(),
                   "machineType": platform.machine(),
                   "env": os.environ,
                   "syspaths": sys.path,
                   "executable": sys.executable}
    return machineDict


def user(lower=True):
    """Returns the current user name

    :param lower: if the username should be returned as lowercase
    :type lower: bool
    :rtype: str
    """
    username = getpass.getuser()
    return username.lower() if lower else username


def isMac():
    """
    :rtype: bool
    """
    plat = platform.system().lower()
    return plat.startswith('mac') or plat.startswith('os') or plat.startswith('darwin')


def isWindows():
    """
    :rtype: bool
    """
    return platform.system().lower().startswith('win')


def isLinux():
    """
    :rtype: bool
    """
    return platform.system().lower().startswith('lin')


def currentOS():
    """ Gets current operating system

    :return: Operating system as string
    :rtype: basestring
    """
    if isMac():
        return "Mac"
    elif isWindows():
        return "Windows"
    elif isLinux():
        return "Linux"


def addToEnv(env, newPaths):
    # to cull empty strings or strings with spaces
    paths = [i for i in os.environ.get(env, "").split(os.pathsep) if i]

    for p in newPaths:
        if p not in paths:
            paths.append(p)
    os.environ[env] = os.pathsep.join(paths) + os.pathsep


def addToSysPath(path):
    """Add the specified path to the system path.

    :param path: Path to add.
    :type path: str
    :return True if path was added. False if path does not exist or path was already in sys.path
    :rtype: bool
    """
    if os.path.exists(path) and path not in sys.path:
        sys.path.insert(0, path)
        return True
    return False
