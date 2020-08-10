import os
import sys
import tempfile
import unittest
from zoo.libs.utils import zlogging
from zoovendor import six


logger = zlogging.getLogger(__name__)


def decorating_meta(decorator):
    class DecoratingMetaclass(type):
        def __new__(cls, class_name, bases, namespace):
            for key, value in list(namespace.items()):
                if callable(value):
                    namespace[key] = decorator(value)
            return type.__new__(cls, class_name, bases, namespace)

    return DecoratingMetaclass


def skipUnlessHasattr(obj):
    if not hasattr(obj, 'skip'):
        def decorated(*a, **kw):
            return obj(*a, **kw)

        return decorated

    def decorated(*a, **kw):
        return unittest.skip("{!r} doesn't have {!r}".format(obj, 'skip'))

    return decorated


@six.add_metaclass(decorating_meta(skipUnlessHasattr))
class BaseUnitest(unittest.TestCase):
    """This Class acts as the base for all unitests, supplies a helper method for creating tempfile which
    will be cleaned up once the class has been shutdown.
    If you override the tearDownClass method you must call super or at least clean up the _createFiles set
    """
    _createdFiles = set()
    application = "standalone"

    @classmethod
    def createTemp(cls, suffix):

        temp = tempfile.mkstemp(suffix=suffix)
        cls._createdFiles.add(temp)
        return temp

    @classmethod
    def addTempFile(cls, filepath):
        cls._createdFiles.add(filepath)

    @classmethod
    def tearDownClass(cls):
        super(BaseUnitest, cls).tearDownClass()
        for i in cls._createdFiles:
            if os.path.exists(i):
                os.remove(i)
        cls._createdFiles.clear()


def runTests(directories=None, test=None, test_suite=None, buffer=False, resultClass=None):
    """Run all the tests in the given paths.

    @param directories: A generator or list of paths containing tests to run.
    @param test: Optional name of a specific test to run.
    @param test_suite: Optional TestSuite to run.  If omitted, a TestSuite will be generated.
    """
    if test_suite is None:
        test_suite = getTests(directories, test)

    runner = unittest.TextTestRunner(verbosity=2, resultclass=resultClass)
    runner.failfast = False
    runner.buffer = buffer
    runner.run(test_suite)


def getTests(directories, test=None, testSuite=None, topLevelDir=None):
    """Get a unittest.TestSuite containing all the desired tests.

    :param directories: Optional list of directories with which to search for tests.
    :param test: Optional test path to find a specific test such as 'test_mytest.SomeTestCase.test_function'.
    :param test_suite: Optional unittest.TestSuite to add the discovered tests to.  If omitted a new TestSuite will be
    created.
    :return: The populated TestSuite.
    """
    # Populate a TestSuite with all the tests
    if testSuite is None:
        testSuite = unittest.TestSuite()

    if test:
        # Find the specified test to run
        directories_added_to_path = [os.path.dirname(p) for p in directories]
        discovered_suite = unittest.TestLoader().loadTestsFromName(test)
        if discovered_suite.countTestCases():
            testSuite.addTests(discovered_suite)
    else:
        # Find all tests to run
        directories_added_to_path = []
        for p in directories:
            discovered_suite = unittest.TestLoader().discover(p, top_level_dir=topLevelDir)
            if discovered_suite.countTestCases():
                testSuite.addTests(discovered_suite)
    # Remove the added paths.
    for path in directories_added_to_path:
        if path in sys.path:
            sys.path.remove(path)

    return testSuite
