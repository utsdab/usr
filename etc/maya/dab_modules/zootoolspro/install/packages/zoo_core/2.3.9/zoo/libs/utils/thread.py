import threading

import shutil


class Threaded(object):
    """Threaded base class that contains a threading.Lock member and an
    'exclusive' function decorator that implements exclusive access
    to the contained code using a thread lock.

    """

    def __init__(self):
        self._lock = threading.Lock()

    @staticmethod
    def exclusive(func):
        """Static method intended to be used as a function decorator in derived
        classes.

        :param func: Function to decorate/wrap
        :returns: Wrapper function that executes the function inside the acquired lock

        .. code-block:: python

                @Threaded.exclusive
                def my_method(self, ...):
                    ...
        """

        def wrapper(self, *args, **kwargs):
            """
            Internal wrapper method that executes the function with the specified arguments
            inside the acquired lock

            :param *args: The function parameters
            :param **kwargs: The function named parameters
            :returns: The result of the function call
            """
            with self._lock:
                return func(self, *args, **kwargs)

        return wrapper


def threadedCopy(filepaths):
    """Copies a set of files in a separate thread.

    Uses the :class:`CopyThread` class.

    :param filepaths: is a list of (from_path, to_path) pairs.
    :type filepaths: list(str)

    .. code-block:: python

        paths =[('C:/src/path.txt', 'C:/destination/path.txt'),
        ('C:/src/path1.txt', 'C:/destination/path1.txt'),
        ('C:/src/path2.txt', 'C:/destination/path2.txt')]
        threadedCopy(paths)


    """
    CopyThread(filepaths).start()


class CopyThread(threading.Thread):
    def __init__(self, filepaths):
        super(CopyThread, self).__init__()
        self.filepaths = filepaths

    def run(self):
        for paths in self.filepaths:
            src, dst = paths
            shutil.copyfile(src, dst)
