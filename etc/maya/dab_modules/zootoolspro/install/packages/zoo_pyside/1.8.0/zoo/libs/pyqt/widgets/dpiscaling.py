from zoo.libs.pyqt import utils


class DPIScaling(object):
    """ Used with any QtWidget to add dpiScaling to their methods """

    def setFixedSize(self, size):
        """ Sets fixed size

        :param size: Dpiscaling is automatically applied here
        :return:
        """
        return super(DPIScaling, self).setFixedSize(utils.dpiScale(size))

    def setFixedHeight(self, height):
        """ DpiScaling version of set fixed height

        :param height:
        :return:
        """
        return super(DPIScaling, self).setFixedHeight(utils.dpiScale(height))

    def setFixedWidth(self, width):
        """ DpiScaling version of set fixed width

        :param width:
        :return:
        """
        return super(DPIScaling, self).setFixedWidth(utils.dpiScale(width))

    def setMaximumWidth(self, width):
        """Sets the maximum button size in pixels

        :param size: New fixed size of the widget
        :type size: QtCore.QSize
        """
        return super(DPIScaling, self).setMaximumWidth(utils.dpiScale(width))

    def setMinimumWidth(self, width):
        """Sets the minimum button size in pixels

        :param size: New fixed size of the widget
        :type size: QtCore.QSize
        """
        return super(DPIScaling, self).setMinimumWidth(utils.dpiScale(width))

    def setMaximumHeight(self, height):
        """Sets the maximum button size in pixels

        :param size: New fixed size of the widget
        :type size: QtCore.QSize
        """
        return super(DPIScaling, self).setMaximumHeight(utils.dpiScale(height))

    def setMinimumHeight(self, height):
        """Sets the minimum button size in pixels

        :param size: New fixed size of the widget
        :type size: QtCore.QSize
        """
        return super(DPIScaling, self).setMinimumHeight(utils.dpiScale(height))

