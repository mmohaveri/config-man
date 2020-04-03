class ConfigManError(Exception):
    pass


class InvalidConfigNameError(ConfigManError):
    pass


class IncompatibleTypeError(ConfigManError):
    pass
