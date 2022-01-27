#  Authors: Sylvain MARIE <sylvain.marie@se.com>
#            + All contributors to <https://github.com/smarie/mkdocs-gallery>
#
#  Original idea and code: sphinx-gallery, <https://sphinx-gallery.github.io>
#  License: 3-clause BSD, <https://github.com/smarie/mkdocs-gallery/blob/master/LICENSE>
"""
Backreferences Generator
========================

Parses example file code in order to keep track of used functions
"""
from __future__ import print_function, unicode_literals

from importlib import import_module

from typing import Set

import ast
import codecs
import collections
from html import escape
import inspect
import os
import re
import warnings

from .errors import ExtensionError

from . import mkdocs_compatibility
from .gen_data_model import GalleryScriptResults, AllInformation
from .utils import _replace_by_new_if_needed, _new_file


class DummyClass(object):
    """Dummy class for testing method resolution."""

    def run(self):
        """Do nothing."""
        pass

    @property
    def prop(self):
        """Property."""
        return 'Property'


class NameFinder(ast.NodeVisitor):
    """Finds the longest form of variable names and their imports in code.

    Only retains names from imported modules.
    """

    def __init__(self, global_variables=None):
        super(NameFinder, self).__init__()
        self.imported_names = {}
        self.global_variables = global_variables or {}
        self.accessed_names = set()

    def visit_Import(self, node, prefix=''):
        for alias in node.names:
            local_name = alias.asname or alias.name
            self.imported_names[local_name] = prefix + alias.name

    def visit_ImportFrom(self, node):
        self.visit_Import(node, node.module + '.')

    def visit_Name(self, node):
        self.accessed_names.add(node.id)

    def visit_Attribute(self, node):
        attrs = []
        while isinstance(node, ast.Attribute):
            attrs.append(node.attr)
            node = node.value

        if isinstance(node, ast.Name):
            # This is a.b, not e.g. a().b
            attrs.append(node.id)
            self.accessed_names.add('.'.join(reversed(attrs)))
        else:
            # need to get a in a().b
            self.visit(node)

    def get_mapping(self):
        options = list()
        for name in self.accessed_names:
            local_name_split = name.split('.')
            # first pass: by global variables and object inspection (preferred)
            for split_level in range(len(local_name_split)):
                local_name = '.'.join(local_name_split[:split_level + 1])
                remainder = name[len(local_name):]
                if local_name in self.global_variables:
                    obj = self.global_variables[local_name]
                    class_attr, method = False, []
                    if remainder:
                        for level in remainder[1:].split('.'):
                            last_obj = obj
                            # determine if it's a property
                            prop = getattr(last_obj.__class__, level, None)
                            if isinstance(prop, property):
                                obj = last_obj
                                class_attr, method = True, [level]
                                break
                            try:
                                obj = getattr(obj, level)
                            except AttributeError:
                                break
                            if inspect.ismethod(obj):
                                obj = last_obj
                                class_attr, method = True, [level]
                                break
                    del remainder
                    is_class = inspect.isclass(obj)
                    if is_class or class_attr:
                        # Traverse all bases
                        classes = [obj if is_class else obj.__class__]
                        offset = 0
                        while offset < len(classes):
                            for base in classes[offset].__bases__:
                                # "object" as a base class is not very useful
                                if base not in classes and base is not object:
                                    classes.append(base)
                            offset += 1
                    else:
                        classes = [obj.__class__]
                    for cc in classes:
                        module = inspect.getmodule(cc)
                        if module is not None:
                            module = module.__name__.split('.')
                            class_name = cc.__qualname__
                            # a.b.C.meth could be documented as a.C.meth,
                            # so go down the list
                            for depth in range(len(module), 0, -1):
                                full_name = '.'.join(
                                    module[:depth] + [class_name] + method)
                                options.append(
                                    (name, full_name, class_attr, is_class))
            # second pass: by import (can't resolve as well without doing
            # some actions like actually importing the modules, so use it
            # as a last resort)
            for split_level in range(len(local_name_split)):
                local_name = '.'.join(local_name_split[:split_level + 1])
                remainder = name[len(local_name):]
                if local_name in self.imported_names:
                    full_name = self.imported_names[local_name] + remainder
                    is_class = class_attr = False  # can't tell without import
                    options.append(
                        (name, full_name, class_attr, is_class))
        return options


def _from_import(a, b):
    # imp_line = 'from %s import %s' % (a, b)
    # scope = dict()
    # with warnings.catch_warnings(record=True):  # swallow warnings
    #     warnings.simplefilter('ignore')
    #     exec(imp_line, scope, scope)
    # return scope
    with warnings.catch_warnings(record=True):  # swallow warnings
        warnings.simplefilter('ignore')
        m = import_module(a)
        obj = getattr(m, b)

    return obj


def _get_short_module_name(module_name, obj_name):
    """Get the shortest possible module name."""
    if '.' in obj_name:
        obj_name, attr = obj_name.split('.')
    else:
        attr = None
    # scope = {}
    try:
        # Find out what the real object is supposed to be.
        imported_obj = _from_import(module_name, obj_name)
    except Exception:  # wrong object
        return None
    else:
        real_obj = imported_obj
        if attr is not None and not hasattr(real_obj, attr):  # wrong class
            return None  # wrong object

    parts = module_name.split('.')
    short_name = module_name
    for i in range(len(parts) - 1, 0, -1):
        short_name = '.'.join(parts[:i])
        # scope = {}
        try:
            imported_obj = _from_import(short_name, obj_name)
            # Ensure shortened object is the same as what we expect.
            assert real_obj is imported_obj  # noqa
        except Exception:  # libraries can throw all sorts of exceptions...
            # get the last working module name
            short_name = '.'.join(parts[:(i + 1)])
            break
    return short_name


_regex = re.compile(r':(?:'
                    r'func(?:tion)?|'
                    r'meth(?:od)?|'
                    r'attr(?:ibute)?|'
                    r'obj(?:ect)?|'
                    r'class):`~?(\S*)`'
                    )


def identify_names(script_blocks, global_variables=None, node=''):
    """Build a codeobj summary by identifying and resolving used names."""

    if node == '':  # mostly convenience for testing functions
        c = '\n'.join(txt for kind, txt, _ in script_blocks if kind == 'code')
        node = ast.parse(c)

    # Get matches from the code (AST)
    finder = NameFinder(global_variables)
    if node is not None:
        finder.visit(node)
    names = list(finder.get_mapping())

    # Get matches from docstring inspection
    text = '\n'.join(txt for kind, txt, _ in script_blocks if kind == 'text')
    names.extend((x, x, False, False) for x in re.findall(_regex, text))
    example_code_obj = collections.OrderedDict()  # order is important

    # Make a list of all guesses, in `_embed_code_links` we will break when we find a match
    for name, full_name, class_like, is_class in names:
        if name not in example_code_obj:
            example_code_obj[name] = list()

        # name is as written in file (e.g. np.asarray)
        # full_name includes resolved import path (e.g. numpy.asarray)
        splitted = full_name.rsplit('.', 1 + class_like)
        if len(splitted) == 1:
            splitted = ('builtins', splitted[0])
        elif len(splitted) == 3:  # class-like
            assert class_like  # noqa
            splitted = (splitted[0], '.'.join(splitted[1:]))
        else:
            assert not class_like  # noqa

        module, attribute = splitted

        # get shortened module name
        module_short = _get_short_module_name(module, attribute)
        cobj = {'name': attribute, 'module': module,
                'module_short': module_short or module, 'is_class': is_class}

        example_code_obj[name].append(cobj)

    return example_code_obj


# TODO only:: html ?
THUMBNAIL_TEMPLATE = """
<div class="mkd-glr-thumbcontainer" tooltip="{snippet}">
    <!--div class="figure align-default" id="id1"-->
        <img alt="{title}" src="{thumbnail}" />
        <p class="caption">
            <span class="caption-text">
                <a class="reference internal" href="{example_html}">
                    <span class="std std-ref">{title}</span>
                </a>
            </span>
            <!--a class="headerlink" href="#id1" title="Permalink to this image"></a-->
        </p>
    <!--/div-->
</div>
"""

# TODO something specific here ?
BACKREF_THUMBNAIL_TEMPLATE = THUMBNAIL_TEMPLATE
#  + """
# .. only:: not html
#
#  * :ref:`mkd_glr_{ref_name}`
# """


def _thumbnail_div(script_results: GalleryScriptResults, is_backref: bool = False, check: bool = True):
    """
    Generate MD to place a thumbnail in a gallery.

    Parameters
    ----------
    script_results : GalleryScriptResults
        The results from processing a gallery example

    is_backref : bool
        ?

    check : bool
        ?

    Returns
    -------
    md : str
        The markdown to integrate in the global gallery readme. Note that this is also the case for subsections.
    """
    # Absolute path to the thumbnail
    if check and not script_results.thumb.exists():
        # This means we have done something wrong in creating our thumbnail!
        raise ExtensionError(f"Could not find internal mkdocs-gallery thumbnail file:\n{script_results.thumb}")

    # Relative path to the thumbnail (relative to the gallery, not the subsection)
    thumb = script_results.thumb_rel_root_gallery

    # Relative path to the html tutorial that will be generated from the md
    example_html = script_results.script.md_file_rel_root_gallery.with_suffix("")

    template = BACKREF_THUMBNAIL_TEMPLATE if is_backref else THUMBNAIL_TEMPLATE
    return template.format(snippet=escape(script_results.intro), thumbnail=thumb, title=script_results.script.title,
                           example_html=example_html)


def _write_backreferences(backrefs: Set, seen_backrefs: Set, script_results: GalleryScriptResults):
    """
    Write backreference file including a thumbnail list of examples.

    Parameters
    ----------
    backrefs : set

    seen_backrefs : set

    script_results : GalleryScriptResults

    Returns
    -------

    """
    all_info = script_results.script.gallery.all_info

    for backref in backrefs:
        # Get the backref file to use for this module, according to config
        include_path = _new_file(all_info.get_backreferences_file(backref))

        # Create new or append to existing file
        seen = backref in seen_backrefs
        with codecs.open(str(include_path), 'a' if seen else 'w', encoding='utf-8') as ex_file:
            # If first ref: write header
            if not seen:
                # Be aware that if the number of lines of this heading changes,
                #   the minigallery directive should be modified accordingly
                heading = 'Examples using ``%s``' % backref
                ex_file.write('\n\n' + heading + '\n')
                ex_file.write('^' * len(heading) + '\n')

            # Write the thumbnail
            ex_file.write(_thumbnail_div(script_results, is_backref=True))
            seen_backrefs.add(backref)


def _finalize_backreferences(seen_backrefs, all_info: AllInformation):
    """Replace backref files only if necessary."""
    logger = mkdocs_compatibility.getLogger('mkdocs-gallery')
    if all_info.gallery_conf['backreferences_dir'] is None:
        return

    for backref in seen_backrefs:
        # Get the backref file to use for this module, according to config
        path = _new_file(all_info.get_backreferences_file(backref))
        if path.exists():
            # Simply drop the .new suffix
            _replace_by_new_if_needed(path, md5_mode='t')
        else:
            # No file: warn
            level = all_info.gallery_conf['log_level'].get('backreference_missing', 'warning')
            func = getattr(logger, level)
            func('Could not find backreferences file: %s' % (path,))
            func('The backreferences are likely to be erroneous '
                 'due to file system case insensitivity.')
