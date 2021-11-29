# -*- coding: utf-8 -*-
"""
Backwards-compatility shims for mkdocs. Currently nothing here.
===============================================================

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
