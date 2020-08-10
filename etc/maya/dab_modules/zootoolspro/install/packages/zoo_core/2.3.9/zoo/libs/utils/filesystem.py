import contextlib
import json
import os
import subprocess
import shutil
import errno
import zipfile
import re
import functools
import sys
from zoovendor.six import string_types, StringIO
from zoo.libs.utils import zlogging, commandline

logger = zlogging.getLogger(zlogging.CENTRAL_LOGGER_NAME)

FILENAMEEXP = re.compile(u'[^\w\.-1]', re.UNICODE)


def clearUnMasked(func):
    """Decorator which clears the umask for a method.
    The umask is a permissions mask that gets applied
    whenever new files or folders are created. For I/O methods
    that have a permissions parameter, it is important that the
    umask is cleared prior to execution, otherwise the default
    umask may alter the resulting permissions

    :type func: function
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # set umask to zero, store old umask
        oldMask = os.umask(0)
        try:
            # execute method payload
            return func(*args, **kwargs)
        finally:
            # set mask back to previous value
            os.umask(oldMask)

    return wrapper


def upDirectory(path, depth=1):
    """Walks up the directory structure, use the depth argument to determine how many directories to walk

    :param path: the starting path to walk up
    :type path: str
    :param depth: how many directories to walk
    :type depth: int
    :return: the found directory
    :rtype: str
    """
    _cur_depth = 1
    while _cur_depth < depth:
        path = os.path.dirname(path)
        _cur_depth += 1
    return path


def iterParentPath(childPath):
    """Generator function that walks up directory structure starting at the childPath

    :param childPath: the starting path to walk up
    :type childPath: str
    :rtype: generator(str)
    """
    path = childPath
    while os.path.split(path)[1]:
        path = os.path.split(path)[0]
        yield path


def findParentDirectory(childPath, folder):
    """recursively walks the up the directory structure and returns the first instance of the folder

    :param childPath: the childpath to walk up
    :type childPath: str
    :param folder: the folder name to find.
    :type folder: str
    :return: the first instance of folder once found.
    :rtype: str
    """
    for p in iterParentPath(childPath):
        if os.path.split(p)[-1] == folder:
            return p


def openLocation(path):
    """Opens the parent directory of a file, selecting the file if possible.

    *Note: needs to be tested in win 10 from inside of Maya, current issues

    :param path: the path to the directory or file
    :type path: str
    """
    platform = sys.platform
    if platform == 'win32':
        if os.path.isdir(path):
            subprocess.Popen(["explorer", os.path.dirname(path)], shell=True)
            return
        subprocess.Popen(["explorer", "/select", path], shell=True)
    elif platform == 'darwin':
        if os.path.isdir(path):
            subprocess.Popen(["explorer", os.path.dirname(path)])
            return
        subprocess.Popen(["open" "-R", os.path.dirname(path)])
    else:
        subprocess.Popen(["xdg-open", os.path.dirname(path)])


def openDirectory(directoryPath):
    """Opens the native OS folder to the directory of file name
    similar to os.startfile(filename) but also supporting osx and linux

    *Note: current duplicate of findParentDirectory() Just it is not working from Maya, needs to be fixed
    :param directoryPath: the path to the directory to open
    :type directoryPath: str
    """
    # TODO:  Note: This function is a current duplicate of findParentDirectory()
    # TODO: findParentDirectory() is not working from Maya, needs to be sorted
    if sys.platform == "win32":
        os.startfile(directoryPath)
    else:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, directoryPath])


@clearUnMasked
def copyFile(src, dst, permissions=0o775):
    """Copy file and sets its permissions.

    :param src: Source file
    :param dst: destination 
    :param permissions: Permissions to use for target file. Default permissions will \
                        be readable and writable for all users.
    """
    dirname = os.path.dirname(dst)
    if not os.path.isdir(dirname):
        old_umask = os.umask(0)
        os.makedirs(dirname, permissions)
        os.umask(old_umask)
    shutil.copy(src, dst)
    # os.chmod(dst, permissions)


@contextlib.contextmanager
def retainCwd():
    """Context manager that keeps cwd unchanged afterwards.
    """
    cwd = os.getcwd()
    try:
        yield
    finally:
        os.chdir(cwd)


def batchCopyFiles(paths, permissions=0o775):
    """ Expects the parent folder to have been already created.

    :param paths: source path, destination path
    :type paths: tuple(tuple(str, str))
    :param permissions: OS permissions
    :type permissions: int
    :return: a list of tuples containing source,destination fails
    :rtype: list(tuple(str, str)
    """
    failed = []
    for source, destination in paths:
        try:
            logger.info("Copying %s --> %s..." % (source, destination))
            copyFile(source, destination, permissions=permissions)
        except OSError:
            failed.append((source, destination))
    return failed


def copyDirectory(src, dst, ignorePattern=None):
    """Copies the directory tree using shutil.copytree

    :param src: the Source directory to copy.
    :type src: str
    :param dst: the destination directory.
    :type dst: str
    :raise: OSError
    """
    try:
        if ignorePattern:
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*ignorePattern))
            return
        shutil.copytree(src, dst)

    except OSError as exc:
        if exc.errno == errno.ENOTDIR:
            shutil.copy(src, dst)
        else:
            logger.error("Failed to copy directory {} to destination: {}".format(src, dst), exc_info=True)
            raise


def copyDirectoryContents(src, dst, skipExist=True, overwriteModified=False):
    """Copies the contents of one directory to another including subfolders.
    Will make the destination directory if it doesn't exist
    Kwargs for checking if the file already exists or has been modified

    :param src: The source path a directory path
    :type src: str
    :param dst: The destination path, a directory path, will create if does not exist
    :type dst: str
    :param skipExist: If True will skip if the file already exists
    :type skipExist: bool
    :param overwriteModified: If the file exists but has been modified overwrite
    :type overwriteModified: bool
    """
    if not os.path.exists(dst):
        os.makedirs(dst)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            copyDirectoryContents(s, d, skipExist=True, overwriteModified=False)
        else:  # only copy files if doesn't exit or has been modified
            if skipExist and not os.path.exists(d):
                shutil.copy2(s, d)
            elif overwriteModified and os.path.exists(d) and os.stat(s).st_mtime - os.stat(d).st_mtime > 1:
                shutil.copy2(s, d)
            elif not skipExist and not overwriteModified:
                shutil.copy2(s, d)


class MoveFileContext(object):
    """With context utility to ensures that files that were moved within the scope are moved to their
    original location if an exception was raised during that scope.

    .. code-block:: python

        with MoveFileContext() as FileContext:
            someSourcePath = os.path.expandUser("~/soemfile.config")
                FileContext.move(sourceSourcePath, os.path.join(os.path.dirname(sourcePath), "destination.config"))
                ValueError("raise an error so we revert")

    """

    def __init__(self):
        self._stack = []

    def __enter__(self):
        """Returns the current class instance
        """
        return self

    def move(self, source, destination):
        """Move's a file and keeps track of the source/destination if it succeeded.

        :param source: Source file to move.
        :param destination: New location for that file.
        """
        shutil.move(source, destination)
        self._stack.append((source, destination))

    def __exit__(self, ex_type, value, traceback):
        """
        If some files have been moved, move them back to their original location.
        """
        if (ex_type or value or traceback) and self._stack:
            logger.debug("Reverting file move changes!")
            # Move files back to their original location.
            for source, destination in self._stack:
                logger.debug("Moving {} -> {}".format(destination, source))
                shutil.move(destination, source)


def folderSize(path):
    """Retrieves the total folder size in bytes

    :param path: Returns the total folder size by walking the directory adding together all child files sizes.
    :type path: str
    :return: size in bytes
    :rtype: int
    """
    totalSize = 0
    for root, dirs, files in os.walk(path):
        for f in files:
            fp = os.path.join(root, f)
            totalSize += os.path.getsize(fp)
    return totalSize


def ensureFolderExists(path, permissions=0o775, placeHolder=False):
    """if the folder doesnt exist then one will be created.
    Function built due to version control mishaps with uncommited empty folders, this folder can generate
    a place holder file.

    :param path: the folderpath to check or create
    :type path: str
    :param permissions: folder permissions mode
    :type permissions: int
    :param placeHolder: if True create a placeholder text file
    :type placeHolder: bool
    :raise OSError: raise OSError if the creation of the folder fails
    """
    if not os.path.exists(path):
        try:
            logger.debug("Creating folder {} [{}]".format(path, permissions))
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
                raise


def createValidfilename(name):
    """Sanitizer for file names which everyone tends to screw up, this function replace spaces and random character with
    underscore.

    .. code-block:: python

        createValidFilename("Some random file name")
        #result: "Some_random_file_name"

    :param name: the name to convert
    :type name: str
    :rtype: the same format as the passed argument type(utf8 etc)
    """
    value = name.strip()
    if isinstance(value, string_types):
        return FILENAMEEXP.sub("_", value)
    else:
        return FILENAMEEXP.sub("_", value.decode("utf-8")).encode("utf-8")


def zipwalk(zfilename):
    """Zip file tree generator.

    For each file entry in a zip archive, this yields
    a two tuple of the zip information and the data
    of the file as a StringIO object.

    zipinfo, filedata

    zipinfo is an instance of zipfile.ZipInfo class
    which gives information of the file contained
    in the zip archive. filedata is a StringIO instance
    representing the actual file data.

    If the file again a zip file, the generator extracts
    the contents of the zip file and walks them.

    Inspired by os.walk .
    """

    tempdir = os.environ.get('TEMP', os.environ.get('TMP', os.environ.get('TMPDIR', '/tmp')))

    try:
        z = zipfile.ZipFile(zfilename, "r")
        for info in z.infolist():
            fname = info.filename
            data = z.read(fname)

            if fname.endswith(".zip"):
                tmpfpath = os.path.join(tempdir, os.path.basename(fname))
                try:
                    open(tmpfpath, 'w+b').write(data)
                except (IOError, OSError):
                    logger.error("Failed to write file, {}".format(tmpfpath), exc_info=True)

                if zipfile.is_zipfile(tmpfpath):
                    try:
                        for x in zipwalk(tmpfpath):
                            yield x
                    except Exception:
                        logger.error("Failed", exc_info=True)
                        raise
                try:
                    os.remove(tmpfpath)
                except:
                    pass
            else:
                yield (info, StringIO(data))
    except (RuntimeError, zipfile.error):
        raise


def directoryTreeToDict(path):
    d = {'name': os.path.basename(path),
         "path": path}
    if os.path.isdir(path):
        d['type'] = "directory"
        d['children'] = [directoryTreeToDict(os.path.join(path, x)) for x in os.listdir(path)]
    else:
        d['type'] = "file"
    return d


if os.name == "nt" and sys.version_info[0] < 3:
    def symlink_ms(source, linkname):
        """Python 2 doesn't have os.symlink on windows so we do it ourselfs
        
        :param source: sourceFile
        :type source: str
        :param linkname: symlink path
        :type linkname: str
        :raises: WindowsError, raises when it fails to create the symlink if the user permissions \
         are incorrect
        """
        import ctypes
        csl = ctypes.windll.kernel32.CreateSymbolicLinkW
        csl.argtypes = (ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32)
        csl.restype = ctypes.c_ubyte
        flags = 1 if os.path.isdir(source) else 0
        try:
            if csl(linkname, source.replace('/', '\\'), flags) == 0:
                raise ctypes.WinError()
        except WindowsError:
            raise WindowsError("Failed to create symbolicLink due to user permissions")


    os.symlink = symlink_ms


def loadJson(filePath, **kwargs):
    """
    This procedure loads and returns the data of a json file

    :return type{dict}: the content of the file
    """
    # load our file
    try:
        with loadFile(filePath) as f:
            data = json.load(f, **kwargs)
    except Exception as er:
        logger.debug("file ({}) not loaded".format(filePath))
        raise er
    # return the files data
    return data


def saveJson(data, filepath, message=True, **kws):
    """This procedure saves given data to a json file

    :param data: The dictionary to save
    :type data: dict
    :param filepath: The full filepath of the json file
    :type filepath: str
    :param message: Report the message to the user?
    :type message: bool
    :param kws: Json Dumps arguments , see standard python docs
    :type kws:
    :return success: File written?
    :rtype success: bool
    """
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, **kws)
    except IOError:
        if message:
            logger.error("Data not saved to file {}".format(filepath))
        return False
    if message:
        logger.info("------->> file correctly saved to : {0}".format(filepath))

    return True


@contextlib.contextmanager
def loadFile(filepath):
    if filepath.endswith(".zip"):
        with zipfile.ZipFile(filepath, 'r') as f:
            yield f
        return
    elif ".zip" in filepath:
        # load from zipfile
        zippath, relativefilePath = filepath.split(".zip")
        zipPath = zippath + ".zip"

        with zipfile.ZipFile(zipPath, 'r') as zip:
            path = relativefilePath.replace("\\", "/").lstrip("/")
            for i in iter(zip.namelist()):
                if path == i:
                    yield zip.open(i)
                    break

        return
    with open(filepath) as f:
        yield f


def getTempDir():
    """Returns the temp directory path on all OS

    :return directory: The temp directory full path
    :rtype directory: str
    """
    return os.environ.get('TEMP', os.environ.get('TMP', os.environ.get('TMPDIR', '/tmp')))


def moveFile(fromFullPath, toFullPath):
    """Moves a file (cut place) from one location to another

    :param fromFullPath: Full path to the file
    :type fromFullPath: str
    :param toFullPath: Full path to the destination
    :type toFullPath: str
    """
    shutil.move(fromFullPath, toFullPath)


def loadFileTxt(filePath):
    """Loads a file as text

    :param filePath: the absolute file path
    :type filePath: str
    :return textFile: the text file
    :rtype textFile: str
    """
    with open(filePath, "r") as fileInstance:
        textFile = fileInstance.read()
    return textFile


def saveFileTxt(formattedText, newfile):
    """Saves a string to a file

    :param formattedText: the text
    :type formattedText: str
    :param newfile: the file to be saved full path
    :type newfile: str
    """
    with open(newfile, "wb") as fileInstance:
        fileInstance.write(formattedText)


def createZipWithProgress(zippath, files):
    """Same as function createZip() but has a stdout progress bar which is useful for commandline work
    :param zippath: the file path for the zip file
    :type zippath: str
    :param files: A Sequence of file paths that will be archived.
    :type files: seq(str)
    """
    dir = os.path.dirname(zippath)
    if not os.path.exists(os.path.join(dir, os.path.dirname(zippath))):
        os.makedirs(os.path.join(dir, os.path.dirname(zippath)))
    logger.debug("writing file: {}".format(zippath))
    length = len(files)
    progressBar = commandline.CommandProgressBar(length, prefix='Progress:', suffix='Complete', barLength=50)
    progressBar.start()
    with zipfile.ZipFile(zippath, "w", zipfile.ZIP_DEFLATED) as archive:
        for p in iter(files):
            logger.debug("Archiving file: {} ----> :{}\n".format(p[0], p[1]))
            archive.write(p[0], p[1])
            progressBar.increment(1)
    logger.debug("finished writing zip file to : {}".format(zippath))


def createZip(zippath, files):
    """Creates a zip file for the files, each path will be stored relative to the zippath which avoids abspath
    :param zippath: the file path for the zip file
    :type zippath: str
    :param files: A Sequence of file paths that will be archived.
    :type files: seq(str)
    """
    dir = os.path.dirname(zippath)
    if not os.path.exists(os.path.join(dir, os.path.dirname(zippath))):
        os.makedirs(os.path.join(dir, os.path.dirname(zippath)))
    logger.debug("writing file: {}".format(zippath))
    with zipfile.ZipFile(zippath, "w", zipfile.ZIP_DEFLATED) as archive:
        for p in iter(files):
            archive.write(p[0], p[1])
    logger.debug("finished writing zip file to : {}".format(zippath))


def checkWritableFile(fullPathFileOrDir):
    """Checks the write-ablity when file permissions can't be checked. Tries to rename file to the exact same name.

    Usually errors when file is in use by the OS.

    This function is currently a hack, if error the file is not writable.

    :param fullPathFileOrDir: the fullpath to the file or the directory
    :type fullPathFileOrDir: str
    :return fileInUseError: returns as True if any file is writable
    :rtype fileInUseError: str
    """
    fileInUseError = False
    try:
        os.rename(fullPathFileOrDir, fullPathFileOrDir)
    except:  # the error is OS dependent, to do it properly should know the error type on all OS
        fileInUseError = True
    return fileInUseError


def checkWritableFiles(fileFullPathList):
    """Checks the write-ablity when file permissions can't be checked. Tries to rename files to the exact same name

    The file may be in use by a program and cannot be modified, is tricky to catch without the rename hack

    Returns error as True if any files in the list aren't writable

    :param fileFullPathList: a list of fullpaths to the files or the directories
    :type fileFullPathList: list(str)
    :return fileInUseError: returns as True if any files in the list aren't writable
    :rtype fileInUseError: bool
    """
    fileInUseError = False
    for fileFullPath in fileFullPathList:  # try to rename all files to the same name, this tests if in use like .abc
        if checkWritableFile(fileFullPath):
            fileInUseError = False
    return fileInUseError


def trailingNumber(name):
    """Returns the trailing number of a string, the name with the number removed, and the padding of the number

    Examples:

        "shaderName" returns "shaderName", None, 0
        "shaderName2" returns "shaderName", 2, 1
        "shader1_Name04" returns "shader1_Name", 4, 2
        "shaderName_99" returns "shaderName_", 99, 2
        "shaderName_0009" returns "shaderName_", 9, 4

    :param name:  The string name incoming
    :type name: str
    :return nameNumberless: The name now with the number removed, will be the same if no number found
    :rtype nameNumberless: str
    :return number: the number if one exists, will be None if no number finishes the string
    :rtype number: int
    :return padding: the padding of the number
    :rtype padding: str
    """
    m = re.search(r'\d+$', name)  # get the number as an object
    if m:
        numberAsString = m.group()  # find the number from it's pointer
        nameNumberless = name[:-len(numberAsString)]  # remove the number at string's end
        padding = len(numberAsString)
        return nameNumberless, int(numberAsString), padding
    return name, None, 0


def uniqueFileName(fullFilePath, countLimit=500):
    """Finds a unique filename if a name already exists by adding a number to the end of the file

    See trailingNumber() documentation for how the numerical numbers are added to the tail of the name.

    :param fullFilePath: Any full path to a filename with an extension
    :type fullFilePath: str
    :param countLimit: since this function uses a while loop, set a limit of loops to stop infinite.
    :type countLimit: int
    :return fullFilePath: The new fullFilePath possibly renamed if matching filename already exists.  "" if count hit
    :rtype fullFilePath: str
    """
    count = 0
    while os.path.exists(fullFilePath):  # while the filename exists on disk, increment is
        directoryPath = os.path.dirname(fullFilePath)  # get the dir of the file
        fileName = os.path.basename(fullFilePath)
        fileNameNoExt = os.path.splitext(fileName)[0]
        extension = os.path.splitext(fileName)[-1]
        # Increment number on the end of the filename
        nameNumberless, number, padding = trailingNumber(fileNameNoExt)
        if not number:
            number = 1
            padding = 2
        else:
            number += 1
        filename = "".join([nameNumberless, str(number).zfill(padding), extension])
        fullFilePath = os.path.join(directoryPath, filename)
        count += 1
        if count > countLimit:
            fullFilePath = ""  # unique name not found
            break
    return fullFilePath


def renameMultipleFilesNoExt(newNameNoExtension, fileFullPathToRenameList, skipThumbnails=True):
    """Rename multiple files/dependency folders useful for .zooScene files and check if all files can be renamed first.

    Files may be in use by a program and cannot be modified, is tricky to catch without the rename hack
    A file may be in use, for example alembic files renaming in the wrong order will cause issues.

    If errors then no files will be renamed.

    :param newNameNoExtension: the new name of the files with no extension, no directory path, filename only
    :type newNameNoExtension: str
    :param fileFullPathToRenameList:  a list of fullpaths to the files or the directories
    :type fileFullPathToRenameList: list(str)
    :param skipThumbnails:  Skips files named thumbnails, "thumbnail.jpg" or "thumbnail.png"
    :type skipThumbnails: bool
    :return renamedList: the renamed files full file path, if empty it's failed
    :rtype renamedList: str
    """
    renamedList = list()
    fileInUseError = checkWritableFiles(fileFullPathToRenameList)
    if fileInUseError:
        # return with no files renamed
        return list()  # usually any file can't rename itself so we take that as "file in use"
    for fileFullPathName in fileFullPathToRenameList:
        fileNameOnly = os.path.basename(fileFullPathName)  # get the extension of the file
        if fileNameOnly == "thumbnail.jpg" or fileNameOnly == "thumbnail.png" and skipThumbnails:  # skip
            continue
        directoryPath = os.path.dirname(fileFullPathName)  # get the dir of the file
        extension = os.path.splitext(fileNameOnly)[1]  # get the filename and no extension
        newNameWithExtension = "".join([newNameNoExtension, extension])  # make the new filename no directory
        newFullPathFileName = os.path.join(directoryPath, newNameWithExtension)  # make the new full path
        # do the rename
        os.rename(fileFullPathName, newFullPathFileName)  # should work this time
        renamedList.append(newFullPathFileName)
    return renamedList
