class UserCancel(Exception):
    def __init__(self, message, errors=None):
        # Call the base class constructor with the parameters it needs
        super(UserCancel, self).__init__(message)
        self.errors = errors
