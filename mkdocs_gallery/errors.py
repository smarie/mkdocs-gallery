from mkdocs.exceptions import PluginError


class MkdocsGalleryError(PluginError):
    """The base class of all errors in this plugin.

    See https://www.mkdocs.org/dev-guide/plugins/#handling-errors.
    """


class ExtensionError(MkdocsGalleryError):
    pass


class ConfigError(MkdocsGalleryError):
    pass
