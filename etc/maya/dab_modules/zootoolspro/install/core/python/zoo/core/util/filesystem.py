import errno
import fnmatch
import json
import os
import zipfile
import logging

logger = logging.getLogger(__name__)


def ensureFolderExists(path, permissions=0o775, placeHolder=False):
    """if the folder doesnt exist then one will be created.
    Function built due to version control mishaps with uncommited empty folders, this folder can generate
    a place holder file.

    :param path: the folder path to check or create
    :type path: str
    :param permissions: folder permissions mode
    :type permissions: int
    :param placeHolder: if True create a placeholder text file
    :type placeHolder: bool
    :raise OSError: raise OSError if the creation of the folder fails
    """
    if not os.path.exists(path):
        try:
            os.makedirs(path, permissions)
            if placeHolder:
                placePath = os.path.join(path, "placeholder")
                if not os.path.exists(placePath):
                    with open(placePath, "wt") as fh:
                        fh.write("Automatically Generated placeHolder file.")
                        fh.write("The reason why this file exists is due to source control system's which do not "
                                 "handle empty folders.")

        except OSError as e:
            # more less work if network race conditions(joy!)
            if e.errno != errno.EEXIST:
                logger.error("Unknown Error Occurred while making path: {}".format(path), exc_info=True)
                raise


def loadJson(filePath):
    """
    This procedure loads and returns the data of a json file

    :return type{dict}: the content of the file
    """
    # load our file
    try:
        data = json.load(filePath)
    except (TypeError, AttributeError):
        with open(filePath) as f:
            data = json.load(f)

    # return the files data
    return data


def saveJson(data, filepath, **kws):
    """
    This procedure saves given data to a json file

    :param data: The json compatible dict to save
    :type data: dict
    :param filepath: The absolute file path to save the data too.
    :type filepath: str
    :param kws: Json Dumps arguments , see standard python docs
    """
    ensureFolderExists(os.path.dirname(filepath))
    with open(filepath, 'w') as f:
        json.dump(data, f, **kws)

    logger.debug("------->> file correctly saved to : {0}".format(filepath))

    return True


def zipdir(directory, outputPath, filters=()):
    """Creates a zip file from a given directory recursively.

    Use 'filters' to supply a fnmatch expression to exclude a directory
    or files.

    :param directory: The directory to save to .zip
    :type directory: str
    :param outputPath: The .zip output path
    :type outputPath: str
    :param filters: A tuple of fnmatch compatible filters.
    :type filters: tuple(str)
    :return: True if the zip was created
    :rtype: bool
    """
    with zipfile.ZipFile(outputPath, 'w', zipfile.ZIP_DEFLATED) as ziph:
        # ziph is zipfile handle
        for root, dirs, files in os.walk(directory):
            if any(fnmatch.fnmatch(root, filterName) for filterName in filters):
                    continue
            for f in files:
                if any(fnmatch.fnmatch(f, filterName) for filterName in filters):
                    continue
                fullpath = os.path.join(root, f)
                ziph.write(fullpath, arcname=fullpath[len(directory) + 1:])
        if os.path.exists(outputPath):
            return True
    return False
