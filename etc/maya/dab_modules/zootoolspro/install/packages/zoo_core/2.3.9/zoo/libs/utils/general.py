import re

def merge(a, b, path=None):
    """Merges two dicts
    http://stackoverflow.com/questions/7204805/dictionaries-of-dictionaries-merge/7205107#7205107
    """
    if path is None:
        path = list()
    for key in b:
        if key not in a:
            a[key] = b[key]
            continue
        if isinstance(a[key], dict) and isinstance(b[key], dict):
            merge(a[key], b[key], path + [str(key)])
        elif a[key] == b[key]:
            pass  # same leaf value
        else:
            raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))

    return a


def numericalSort(data):
    """Numerically sorts a list of strings that may have integers within

    :type data: list(str)
    :rtype: list(str)

    .. code-block:: python

        data = ["ctrl1", "ctrl50", "ctrl2", "ctrl"]
        print numericalSort(data)
        # Result: ['joint', 'joint1', 'joint2', 'joint50'] #
    """
    return sorted(data, key=lambda key: [int(c) if c.isdigit() else c for c in re.split('([0-9]+)', key)])


def humanizeBytes(bytes, precision=1):
    """Return a humanized string representation of a number of bytes.
    Based on: http://code.activestate.com/recipes/577081-humanized-representation-of-a-number-of-bytes

    .. code-block:: python

        humanize_bytes(1)
        # '1 byte'
        humanizeBytes(1024)
        # '1.0 kB'
        humanizeBytes(1024*123)
        # '123.0 kB'
        humanizeBytes(1024*12342)
        # '12.1 MB'
        humanizeBytes(1024*12342,2)
        # '12.05 MB'
        humanizeBytes(1024*1234,2)
        # '1.21 MB'
        humanizeBytes(1024*1234*1111,2)
        # '1.31 GB'
        humanizeBytes(1024*1234*1111,1)
        # '1.3 GB'

    """
    if bytes == 1:
        return '1 byte'
    if bytes < 1024:
        return '%.*f %s' % (precision, bytes, "bytes")

    suffixes = ['KB', 'MB', 'GB', 'TB', 'PB']
    multiple = 1024.0  # .0 to force float on python 2
    for suffix in suffixes:
        bytes /= multiple
        if bytes < multiple:
            return '%.*f %s' % (precision, bytes, suffix)
    return '%.*f %s' % (precision, bytes, suffix)


def getDuplicates(seq):
    """Return's all the duplicate value in `seq`

    :param seq: the sequence of possible duplicates
    :type seq: list or tuple
    :return: a list of duplicate values from `seq`
    :rtype: list
    """
    seen = set()
    dups = []
    for x in seq:
        if x in seen:
            dups.append(x)
        seen.add(x)
    return dups


def fuzzyFinder(input, collection):
    """ A poor person fuzzy finder function.

    :param input: A partial string which is typically entered by a user.
    :type input: str.
    :param collection: A collection of strings which will be filtered based on the `input`.
    :type collection: iterable.
    :returns: A generator object that produces a list of suggestions narrowed down from `collection` using the `input`.
    :rtype: generator.

    .. code-block:: python

        list(fuzzyFinder("te", ["gete", "test", "hello", "job", "lbsknasdvte", "3rya8d^&%()te)VHF"]))
        # result ['test', 'gete', 'lbsknasdvte', '3rya8d^&%()te)VHF']
    """
    regex = re.compile('.*?'.join(map(re.escape, input)))
    suggestions = set()
    for item in collection:
        r = regex.search(item)
        if r:
            suggestions.add((len(r.group()), r.start(), item))

    return (z[-1] for z in sorted(suggestions))


def isIteratable(obj):
    """Determines if the object is an iterable.

    This is done by attempting to iterate on the obj and if it raise's a 
    type error then return False else True

    :return: returns True if the obj is iterable.
    :rtype: bool
    """
    try:
        for i in iter(obj):
            return True
    except TypeError:
        return False


def chunks(iteratable, size, overlap=0):
    """Yield successive sized chunks from `iteratable`.
    """
    for i in range(0, len(iteratable)-overlap, size-overlap):
        yield iteratable[i:i + size]


class ObjectDict(dict):
    """Wrapper of the standard python dict operate like an object.

    .. code-block:: python

        a = ObjectDict({'channelBox': False,
                 'default': u'',
                 'isDynamic': True,
                 'keyable': False,
                 'locked': False,
                 'max': None,
                 'min': None,
                 'name': u'id',
                 'softMax': None,
                 'softMin': None,
                 'Type': 13, # type found from zoo.libs.maya.api.attrtypes
                 'value': u'mid'}
                 )
        a.max
        a.min

    """

    def __init__(self, **kwargs):
        super(ObjectDict, self).__init__(**kwargs)

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            return super(ObjectDict, self).__getattribute__(item)

    def __setattr__(self, key, value):
        self[key] = value
        # super(ObjectDict, self).__setattr__(key, value)

    def __delattr__(self, item):
        if item in self:
            del self[item]
            return
        super(ObjectDict, self).__delattr__(item)


def compareDictionaries(source, target):
    """ Compare the two dictionaries source and target.

    Target will get the new changes from source.

    :param source: The source dictionary with the original zoo key entries
    :type source: dict
    :param target: The target dictionary that will get the new changes from source
    :type target: dict
    :return messageLog: A message log of any changes that have occurred
    :rtype messageLog: str
    """
    messageLog = ""
    for k, v in source.items():
        existing = target.get(k)
        if existing is None:
            messageLog += "New key found while comparing user to default dictionary. " \
                         "Copying over [\"{}\": \"{}\"] \n".format(k, v)
            target[k] = v
            existing = v

        if isinstance(v, dict):
            t, m = compareDictionaries(v, existing)
            messageLog += m

    return target, messageLog

