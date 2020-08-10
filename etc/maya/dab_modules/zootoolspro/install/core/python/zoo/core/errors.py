from zoovendor import six


class PackageAlreadyExists(Exception):
    """Raised when the package requested already exist.
    """
    pass


class MissingPackageVersion(Exception):
    """Raised when the requested package doesn't exist in the packages location
    """
    pass


class MissingPackage(Exception):
    pass


class DescriptorMissingKeys(Exception):
    """Raised when the provided descriptor keys doesn't
    meet the required descriptor keys
    """
    pass


class UnsupportedDescriptorType(Exception):
    """Raised when the provided descriptor information doesn't match
    any existing descriptors
    """
    pass


class MissingGitPython(Exception):
    """Error Raised when git python installed in the current python environment
    """

    def __init__(self, *args, **kwargs):
        msg = "Must have gitpython install in current environment to work with git"
        super(MissingGitPython, self).__init__(msg, *args, **kwargs)


if six.PY2:
    class FileNotFoundError(Exception):
        """Raised When a File doesn't exist on disk
        """

        def __init__(self, *args):
            super(FileNotFoundError, self).__init__(*args)


    class FileExistsError(Exception):
        def __init__(self, *args):
            super(FileExistsError, self).__init__(*args)
else:
    FileNotFoundError = FileNotFoundError
    FileExistsError = FileExistsError


class InvalidPackagePath(Exception):
    """Raised when The package path requested isn't compatible with zootools.
    """
    pass


class MissingEnvironmentPath(Exception):
    """Raised when the package_version.config doesn't exist
    """
    pass


class GitTagAlreadyExists(Exception):
    """Raised request for tag creation already exists
    """
    pass


class MissingCliArgument(Exception):
    pass
