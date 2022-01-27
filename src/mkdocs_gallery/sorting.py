#  Authors: Sylvain MARIE <sylvain.marie@se.com>
#            + All contributors to <https://github.com/smarie/mkdocs-gallery>
#
#  Original idea and code: sphinx-gallery, <https://sphinx-gallery.github.io>
#  License: 3-clause BSD, <https://github.com/smarie/mkdocs-gallery/blob/master/LICENSE>
"""
Sorters for mkdocs-gallery (sub)sections
========================================

Sorting key functions for gallery subsection folders and section files.
"""

from __future__ import division, absolute_import, print_function

from enum import Enum
from pathlib import Path

from typing import Type, Iterable

import os
import types

from .errors import ConfigError

from .gen_single import extract_intro_and_title
from .py_source_parser import split_code_and_text_blocks


class _SortKey(object):
    """Base class for section order key classes."""

    def __repr__(self):
        return '<%s>' % (self.__class__.__name__,)


class ExplicitOrder(_SortKey):
    """Sorting key for all gallery subsections.

    This requires all folders to be listed otherwise an exception is raised.

    Parameters
    ----------
    ordered_list : list, tuple, or :term:`python:generator`
        Hold the paths of each galleries' subsections.

    Raises
    ------
    ValueError
        Wrong input type or Subgallery path missing.
    """

    def __init__(self, ordered_list: Iterable[str]):
        if not isinstance(ordered_list, (list, tuple, types.GeneratorType)):
            raise ConfigError("ExplicitOrder sorting key takes a list, "
                              "tuple or Generator, which hold"
                              "the paths of each gallery subfolder")

        self.ordered_list = list(os.path.normpath(path)
                                 for path in ordered_list)

    def __call__(self, item: Path):
        if item.name in self.ordered_list:
            return self.ordered_list.index(item.name)
        else:
            raise ConfigError('If you use an explicit folder ordering, you '
                              'must specify all folders. Explicit order not '
                              'found for {}'.format(item.name))

    def __repr__(self):
        return '<%s : %s>' % (self.__class__.__name__, self.ordered_list)


class NumberOfCodeLinesSortKey(_SortKey):
    """Sort examples by the number of code lines."""

    def __call__(self, file: Path):
        file_conf, script_blocks = split_code_and_text_blocks(file)
        amount_of_code = sum([len(bcontent)
                              for blabel, bcontent, lineno in script_blocks
                              if blabel == 'code'])
        return amount_of_code


class FileSizeSortKey(_SortKey):
    """Sort examples by file size."""

    def __call__(self, file: Path):
        # src_file = os.path.normpath(str(file))
        # return int(os.stat(src_file).st_size)
        return file.stat().st_size


class FileNameSortKey(_SortKey):
    """Sort examples by file name."""

    def __call__(self, file: Path):
        return file.name


class ExampleTitleSortKey(_SortKey):
    """Sort examples by example title."""

    def __call__(self, file: Path):
        _, script_blocks = split_code_and_text_blocks(file)
        _, title = extract_intro_and_title(file, script_blocks[0][1])
        return title


class SortingMethod(Enum):
    """
    All known sorting methods.
    """
    ExplicitOrder = ExplicitOrder
    NumberOfCodeLinesSortKey = NumberOfCodeLinesSortKey
    FileSizeSortKey = FileSizeSortKey
    FileNameSortKey = FileNameSortKey
    ExampleTitleSortKey = ExampleTitleSortKey

    def __call__(self, *args, **kwargs):
        """When enum member is called, return the class"""
        return self.value(*args, **kwargs)

    @classmethod
    def all_names(cls):
        return [s.name for s in cls]

    @classmethod
    def from_str(cls, name) -> "SortingMethod":
        try:
            return cls[name]
        except KeyError:
            raise ValueError(f"Unknown sorting method {name!r}. Available methods: {cls.all_names()}")


def str_to_sorting_method(name: str) -> Type:
    """Return the sorting method class associated with the fiven name."""
    return SortingMethod.from_str(name).value
