import re


def camelToNice(strInput, space=" "):
    """ Camel case to nicely formatted string

    eg. theQuickBrownFox ==> the Quick Brown Fox

    :param strInput: String to convert
    :type strInput: basestring
    :param space:
    :return:
    :rtype: basestring
    """
    splitted = re.sub('(?!^)([A-Z][a-z]+)', r' \1', strInput).split()
    ret = space.join(splitted)

    return ret
