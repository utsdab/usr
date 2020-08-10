from Qt import QtWidgets
__all__ = ("TaggedAction", )


class TaggedAction(QtWidgets.QAction):
    def __init__(self, label, parent=None):
        super(TaggedAction, self).__init__(label, parent)
        # sequence of tags which will be used for filtering this action
        self.tags = set()

    def hasTag(self, tag):
        """Searches this instance tags and does a contains(in) operator on each tag, returns True if the tag is valid
        else False.

        :param tag: the partial or full tag to search for
        :type tag: str
        :rtype: bool
        """
        # tag = tag.lower()
        for t in self.tags:
            if tag in t:
                return True
        return False

    def hasAnyTag(self, tags):
        for t in tags:
            for i in self.tags:
                if t in i:
                    return True
        return False
