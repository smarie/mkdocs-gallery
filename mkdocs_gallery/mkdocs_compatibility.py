#  Authors: Sylvain MARIE <sylvain.marie@se.com>
#            + All contributors to <https://github.com/smarie/mkdocs-gallery>
#
#  Original idea and code: sphinx-gallery, <https://sphinx-gallery.github.io>
#  License: 3-clause BSD, <https://github.com/smarie/mkdocs-gallery/blob/master/LICENSE>
"""
Backwards-compatility shims for mkdocs. Only logger is here for now.
"""

import logging
from mkdocs.utils import warning_filter


def red(msg):
    # TODO investigate how we can do this in mkdocs console
    return msg


def getLogger(name="mkdocs-gallery"):
    """From https://github.com/fralau/mkdocs-mermaid2-plugin/pull/19/. """
    log = logging.getLogger("mkdocs.plugins." + name)
    log.addFilter(warning_filter)

    # todo what about colors ? currently we remove the argument in each call

    # the verbose method does not exist
    log.verbose = log.debug

    return log


# status_iterator = sphinx.util.status_iterator
