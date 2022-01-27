#  Authors: Sylvain MARIE <sylvain.marie@se.com>
#            + All contributors to <https://github.com/smarie/mkdocs-gallery>
#
#  Original idea and code: sphinx-gallery, <https://sphinx-gallery.github.io>
#  License: 3-clause BSD, <https://github.com/smarie/mkdocs-gallery/blob/master/LICENSE>
"""
Common errors
"""

from mkdocs.exceptions import PluginError


class MkdocsGalleryError(PluginError):
    """The base class of all errors in this plugin.

    See https://www.mkdocs.org/dev-guide/plugins/#handling-errors.
    """


class ExtensionError(MkdocsGalleryError):
    pass


class ConfigError(MkdocsGalleryError):
    pass
