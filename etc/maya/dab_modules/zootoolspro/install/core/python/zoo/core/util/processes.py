import subprocess
import sys


def subprocessCheckOutput(*args, **kwargs):
    """called subprocess.Popen with communicate()

    :param args: subprocess.Popen arguments
    :type args: tuple
    :param kwargs: subprocess.Popen keyword arguments
    :type kwargs: dict
    :return: str output from subprocess.Popen.communicate
    :rtype: str
    """
    process = subprocess.Popen(
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.PIPE,
        *args,
        **kwargs

    )
    if sys.platform == "win32":
        process.stdin.close()
    output = process.communicate()
    failCode = process.poll()
    if failCode:
        raise OSError(output)
    return output


def checkOutput(*args, **kwargs):
    """Helper function that handles sub processing safely on win32
    which requires extra flags

    :param args: The arguments to pass to subprocess
    :type args: list
    :param kwargs: The keyword arguments to pass to subprocess
    :type kwargs: dict
    :return: The subprocess output string
    :rtype: str
    """
    if sys.platform == "win32":
        info = subprocess.STARTUPINFO()
        info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        info.wShowWindow = subprocess.SW_HIDE
    return subprocessCheckOutput(*args, **kwargs)
