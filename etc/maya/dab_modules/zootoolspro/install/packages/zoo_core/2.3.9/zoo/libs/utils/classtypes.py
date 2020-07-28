class Singleton(type):
    """Singleton metaclass that overrides the __call__ method and always returns a single class instance
    of the cls.
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
