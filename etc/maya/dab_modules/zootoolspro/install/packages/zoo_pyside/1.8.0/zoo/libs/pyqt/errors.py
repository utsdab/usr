from widgets import messagebox as msg


class QtBaseException(Exception):
    """
    Custom Exception base class used to handle exception with our on subset of options
    """

    def __init__(self, message, displayPopup=False, *args):
        """initializes the exception, use cause to display the cause of the exception

        :param message: The exception to display
        :param cause: the cause of the error eg. a variable/class etc
        :param args: std Exception args
        """
        self.message = message
        if displayPopup:
            self.showDialog()

        super(self.__class__, self).__init__(message, *args)

    def showDialog(self):
        messageBox = msg.MessageBox()
        messageBox.setText(self.message)
        messageBox.exec_()
