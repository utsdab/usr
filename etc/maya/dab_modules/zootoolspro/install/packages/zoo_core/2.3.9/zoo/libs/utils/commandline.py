import sys


class CommandProgressBar(object):
    def __init__(self, total, prefix, suffix, decimals=1, barLength=50):
        """Call in a loop to create terminal progress bar

        :param total: the total iterations
        :type total int
        :param prefix:  prefix
        :type prefix str
        :param suffix:  suffix
        :type suffix str
        :param decimals: positive number of decimals in percent complete
        :type decimals: int
        :param barLength: character length of bar
        :type barLength: int
        """
        self.total = total
        self.prefix = prefix
        self.suffix = suffix
        self.decimals = decimals
        self.barLength = barLength
        self.progress = 0

    def increment(self, value=0):
        self.progress += value

        str_format = "{0:." + str(self.decimals) + "f}"
        percents = str_format.format(100 * (self.progress / float(self.total)))
        filled_length = int(round(self.barLength * self.progress / float(self.total)))
        bar = '' * filled_length + '-' * (self.barLength - filled_length)

        sys.stdout.write('\r{} |{}| {}{} {}'.format(self.prefix, bar, percents, '%', self.suffix))

        if self.progress == self.total:
            sys.stdout.write('\n')
        sys.stdout.flush()

    def start(self):
        self.increment(0)
