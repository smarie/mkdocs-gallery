#  Authors: Sylvain MARIE <sylvain.marie@se.com>
#            + All contributors to <https://github.com/smarie/mkdocs-gallery>
#
#  Original idea and code: sphinx-gallery, <https://sphinx-gallery.github.io>
#  License: 3-clause BSD, <https://github.com/smarie/mkdocs-gallery/blob/master/LICENSE>
"""
Generator for a whole gallery.
"""

from __future__ import division, print_function, absolute_import

from ast import literal_eval

from importlib.util import spec_from_file_location, module_from_spec

from typing import Dict, Iterable, Tuple, List, Set

import codecs
import copy
from datetime import timedelta, datetime
from difflib import get_close_matches
from importlib import import_module
import re
import os
from pathlib import Path
from xml.sax.saxutils import quoteattr, escape  # noqa  # indeed this is just quoting and escaping

from .errors import ConfigError, ExtensionError
from . import mkdocs_compatibility
from .gen_data_model import AllInformation, GalleryScript, GalleryScriptResults, GalleryBase
from .mkdocs_compatibility import red
from .utils import _replace_by_new_if_needed, _has_optipng, _new_file
from .backreferences import _finalize_backreferences
from .gen_single import MKD_GLR_SIG, _get_memory_base, generate
from .scrapers import _scraper_dict, _reset_dict, _import_matplotlib
from .downloads import generate_zipfiles
from .sorting import NumberOfCodeLinesSortKey, str_to_sorting_method
from .binder import check_binder_conf


_KNOWN_CSS = ('sg_gallery', 'sg_gallery-binder', 'sg_gallery-dataframe',
              'sg_gallery-rendered-html')


class DefaultResetArgv:
    def __repr__(self):
        return "DefaultResetArgv"

    def __call__(self, script: GalleryScript):
        return []


DEFAULT_GALLERY_CONF = {
    'filename_pattern': re.escape(os.sep) + 'plot',
    'ignore_pattern': r'__init__\.py',
    'examples_dirs': os.path.join('..', 'examples'),
    'reset_argv': DefaultResetArgv(),
    'subsection_order': None,
    'within_subsection_order': NumberOfCodeLinesSortKey,
    'gallery_dirs': 'auto_examples',
    'backreferences_dir': None,
    'doc_module': (),
    'reference_url': {},
    'capture_repr': ('_repr_html_', '__repr__'),
    'ignore_repr_types': r'',
    # Build options
    # -------------
    # 'plot_gallery' also accepts strings that evaluate to a bool, e.g. "True",
    # "False", "1", "0" so that they can be easily set via command line
    # switches of sphinx-build
    'plot_gallery': True,
    'download_all_examples': True,
    'abort_on_example_error': False,
    'only_warn_on_example_error': False,
    'failing_examples': {},  # type: Set[str]
    'passing_examples': [],
    'stale_examples': [],  # type: List[str]  # ones that did not need to be run due to md5sum
    'run_stale_examples': False,
    'expected_failing_examples': set(),  # type: Set[str]
    'thumbnail_size': (400, 280),  # Default CSS does 0.4 scaling (160, 112)
    'min_reported_time': 0,
    'binder': {},
    'image_scrapers': ('matplotlib',),
    'compress_images': (),
    'reset_modules': ('matplotlib', 'seaborn'),
    'first_notebook_cell': '%matplotlib inline',
    'last_notebook_cell': None,
    'notebook_images': False,
    # 'pypandoc': False,
    'remove_config_comments': False,
    'show_memory': False,
    'show_signature': True,
    'junit': '',
    'log_level': {'backreference_missing': 'warning'},
    'inspect_global_variables': True,
    'css': _KNOWN_CSS,
    'matplotlib_animations': False,
    'image_srcset': [],
    'default_thumb_file': None,
    'line_numbers': False,
}

logger = mkdocs_compatibility.getLogger('mkdocs-gallery')


def _bool_eval(x):
    if isinstance(x, str):
        try:
            x = literal_eval(x)
        except TypeError:
            pass
    return bool(x)


def parse_config(mkdocs_gallery_conf, mkdocs_conf, check_keys=True):
    """Process the Sphinx Gallery configuration."""

    # Import the base configuration script
    gallery_conf = load_base_conf(mkdocs_gallery_conf.pop("conf_script", None))
    # Transform all strings to paths: not needed

    # Merge configs
    for opt_name, opt_value in mkdocs_gallery_conf.items():
        # Did the user override the option in mkdocs.yml ? (for SubConfigswe do not receive None but {})
        if opt_value is None or (opt_name in ('binder',) and len(opt_value) == 0):
            continue  # Not user-specified, skip

        # User has overridden it. Use it
        gallery_conf[opt_name] = opt_value

    if isinstance(gallery_conf.get("doc_module", None), list):
        gallery_conf["doc_module"] = tuple(gallery_conf["doc_module"])

    gallery_conf = _complete_gallery_conf(gallery_conf, mkdocs_conf=mkdocs_conf, check_keys=check_keys)

    return gallery_conf


def load_base_conf(script: Path = None) -> Dict:
    if script is None:
        return dict()

    try:
        spec = spec_from_file_location("__mkdocs_gallery_conf", script)
        foo = module_from_spec(spec)
        spec.loader.exec_module(foo)
    except ImportError:
        raise ExtensionError(f"Error importing base configuration from `base_conf_py` {script}")

    try:
        return foo.conf
    except AttributeError:
        raise ExtensionError(f"Error loading base configuration from `base_conf_py` {script}, module does not contain "
                             f"a `conf` variable.")


def _complete_gallery_conf(mkdocs_gallery_conf, mkdocs_conf, lang='python',
                           builder_name='html', app=None, check_keys=True):
    gallery_conf = copy.deepcopy(DEFAULT_GALLERY_CONF)
    options = sorted(gallery_conf)
    extra_keys = sorted(set(mkdocs_gallery_conf) - set(options))
    if extra_keys and check_keys:
        msg = 'Unknown key(s) in mkdocs_gallery_conf:\n'
        for key in extra_keys:
            options = get_close_matches(key, options, cutoff=0.66)
            msg += repr(key)
            if len(options) == 1:
                msg += ', did you mean %r?' % (options[0],)
            elif len(options) > 1:
                msg += ', did you mean one of %r?' % (options,)
            msg += '\n'
        raise ConfigError(msg.strip())
    gallery_conf.update(mkdocs_gallery_conf)
    if mkdocs_gallery_conf.get('find_mayavi_figures', False):
        logger.warning(
            "Deprecated image scraping variable `find_mayavi_figures`\n"
            "detected, use `image_scrapers` instead as:\n\n"
            "   image_scrapers=('matplotlib', 'mayavi')",
            type=DeprecationWarning)
        gallery_conf['image_scrapers'] += ('mayavi',)

    # Text to Class for sorting methods
    _order = gallery_conf['subsection_order']
    if isinstance(_order, str):
        # the option was passed from the mkdocs.yml file
        gallery_conf['subsection_order'] = str_to_sorting_method(_order)

    _order = gallery_conf['within_subsection_order']
    if isinstance(_order, str):
        # the option was passed from the mkdocs.yml file
        gallery_conf['within_subsection_order'] = str_to_sorting_method(_order)

    # XXX anything that can only be a bool (rather than str) should probably be
    # evaluated this way as it allows setting via -D on the command line
    for key in ('run_stale_examples',):
        gallery_conf[key] = _bool_eval(gallery_conf[key])
    # gallery_conf['src_dir'] = mkdocs_conf['docs_dir']
    # gallery_conf['app'] = app

    # Check capture_repr
    capture_repr = gallery_conf['capture_repr']
    supported_reprs = ['__repr__', '__str__', '_repr_html_']
    if isinstance(capture_repr, tuple):
        for rep in capture_repr:
            if rep not in supported_reprs:
                raise ConfigError("All entries in 'capture_repr' must be one "
                                  "of %s, got: %s" % (supported_reprs, rep))
    else:
        raise ConfigError("'capture_repr' must be a tuple, got: %s"
                          % (type(capture_repr),))
    # Check ignore_repr_types
    if not isinstance(gallery_conf['ignore_repr_types'], str):
        raise ConfigError("'ignore_repr_types' must be a string, got: %s"
                          % (type(gallery_conf['ignore_repr_types']),))

    # deal with show_memory
    gallery_conf['memory_base'] = 0.
    if gallery_conf['show_memory']:
        if not callable(gallery_conf['show_memory']):  # True-like
            try:
                from memory_profiler import memory_usage  # noqa
            except ImportError:
                logger.warning("Please install 'memory_profiler' to enable "
                               "peak memory measurements.")
                gallery_conf['show_memory'] = False
            else:
                def call_memory(func):
                    mem, out = memory_usage(func, max_usage=True, retval=True,
                                            multiprocess=True)
                    try:
                        mem = mem[0]  # old MP always returned a list
                    except TypeError:  # 'float' object is not subscriptable
                        pass
                    return mem, out
                gallery_conf['call_memory'] = call_memory
                gallery_conf['memory_base'] = _get_memory_base(gallery_conf)
        else:
            gallery_conf['call_memory'] = gallery_conf['show_memory']
    if not gallery_conf['show_memory']:  # can be set to False above
        def call_memory(func):
            return 0., func()
        gallery_conf['call_memory'] = call_memory
    assert callable(gallery_conf['call_memory'])  # noqa

    # deal with scrapers
    scrapers = gallery_conf['image_scrapers']
    if not isinstance(scrapers, (tuple, list)):
        scrapers = [scrapers]
    scrapers = list(scrapers)
    for si, scraper in enumerate(scrapers):
        if isinstance(scraper, str):
            if scraper in _scraper_dict:
                scraper = _scraper_dict[scraper]
            else:
                orig_scraper = scraper
                try:
                    scraper = import_module(scraper)
                    scraper = scraper._get_sg_image_scraper
                    scraper = scraper()
                except Exception as exp:
                    raise ConfigError('Unknown image scraper %r, got:\n%s'
                                      % (orig_scraper, exp))
            scrapers[si] = scraper
        if not callable(scraper):
            raise ConfigError('Scraper %r was not callable' % (scraper,))
    gallery_conf['image_scrapers'] = tuple(scrapers)
    del scrapers
    # Here we try to set up matplotlib but don't raise an error,
    # we will raise an error later when we actually try to use it
    # (if we do so) in scrapers.py.
    # In principle we could look to see if there is a matplotlib scraper
    # in our scrapers list, but this would be backward incompatible with
    # anyone using or relying on our Agg-setting behavior (e.g., for some
    # custom matplotlib SVG scraper as in our docs).
    # Eventually we can make this a config var like matplotlib_agg or something
    # if people need us not to set it to Agg.
    try:
        _import_matplotlib()
    except (ImportError, ValueError):
        pass

    # compress_images
    compress_images = gallery_conf['compress_images']
    if isinstance(compress_images, str):
        compress_images = [compress_images]
    elif not isinstance(compress_images, (tuple, list)):
        raise ConfigError('compress_images must be a tuple, list, or str, '
                          'got %s' % (type(compress_images),))
    compress_images = list(compress_images)
    allowed_values = ('images', 'thumbnails')
    pops = list()
    for ki, kind in enumerate(compress_images):
        if kind not in allowed_values:
            if kind.startswith('-'):
                pops.append(ki)
                continue
            raise ConfigError('All entries in compress_images must be one of '
                              '%s or a command-line switch starting with "-", '
                              'got %r' % (allowed_values, kind))
    compress_images_args = [compress_images.pop(p) for p in pops[::-1]]
    if len(compress_images) and not _has_optipng():
        logger.warning(
            'optipng binaries not found, PNG %s will not be optimized'
            % (' and '.join(compress_images),))
        compress_images = ()
    gallery_conf['compress_images'] = compress_images
    gallery_conf['compress_images_args'] = compress_images_args

    # deal with resetters
    resetters = gallery_conf['reset_modules']
    if not isinstance(resetters, (tuple, list)):
        resetters = [resetters]
    resetters = list(resetters)
    for ri, resetter in enumerate(resetters):
        if isinstance(resetter, str):
            if resetter not in _reset_dict:
                raise ConfigError('Unknown module resetter named %r'
                                  % (resetter,))
            resetters[ri] = _reset_dict[resetter]
        elif not callable(resetter):
            raise ConfigError('Module resetter %r was not callable'
                              % (resetter,))
    gallery_conf['reset_modules'] = tuple(resetters)

    lang = lang if lang in ('python', 'python3', 'default') else 'python'
    gallery_conf['lang'] = lang
    del resetters

    # Ensure the first cell text is a string if we have it
    first_cell = gallery_conf.get("first_notebook_cell")
    if (not isinstance(first_cell, str)) and (first_cell is not None):
        raise ConfigError("The 'first_notebook_cell' parameter must be type "
                          "str or None, found type %s" % type(first_cell))
    # Ensure the last cell text is a string if we have it
    last_cell = gallery_conf.get("last_notebook_cell")
    if (not isinstance(last_cell, str)) and (last_cell is not None):
        raise ConfigError("The 'last_notebook_cell' parameter must be type str"
                          " or None, found type %s" % type(last_cell))
    # Check pypandoc
    # pypandoc = gallery_conf['pypandoc']
    # if not isinstance(pypandoc, (dict, bool)):
    #     raise ConfigError("'pypandoc' parameter must be of type bool or dict,"
    #                       "got: %s." % type(pypandoc))
    # gallery_conf['pypandoc'] = dict() if pypandoc is True else pypandoc
    # has_pypandoc, version = _has_pypandoc()
    # if isinstance(gallery_conf['pypandoc'], dict) and has_pypandoc is None:
    #     logger.warning("'pypandoc' not available. Using mkdocs-gallery to "
    #                    "convert md text blocks to markdown for .ipynb files.")
    #     gallery_conf['pypandoc'] = False
    # elif isinstance(gallery_conf['pypandoc'], dict):
    #     logger.info("Using pandoc version: %s to convert rst text blocks to "
    #                 "markdown for .ipynb files" % (version,))
    # else:
    #     logger.info("Using mkdocs-gallery to convert rst text blocks to "
    #                 "markdown for .ipynb files.")
    # if isinstance(pypandoc, dict):
    #     accepted_keys = ('extra_args', 'filters')
    #     for key in pypandoc:
    #         if key not in accepted_keys:
    #             raise ConfigError("'pypandoc' only accepts the following key "
    #                               "values: %s, got: %s."
    #                               % (accepted_keys, key))

    # Make it easy to know which builder we're in
    # gallery_conf['builder_name'] = builder_name
    # gallery_conf['titles'] = {}

    # Ensure 'backreferences_dir' is str, Path or None
    backref = gallery_conf['backreferences_dir']
    if (not isinstance(backref, (str, Path))) and \
            (backref is not None):
        raise ConfigError("The 'backreferences_dir' parameter must be of type "
                          "str, Path or None, "
                          "found type %s" % type(backref))
    # if 'backreferences_dir' is str, make Path
    # NO: we need it to remain a str so that plugin.py works (it uses it to exclude the dir in serve mode)
    # if isinstance(backref, str):
    #     gallery_conf['backreferences_dir'] = Path(backref)

    # binder
    gallery_conf['binder'] = check_binder_conf(gallery_conf['binder'])

    if not isinstance(gallery_conf['css'], (list, tuple)):
        raise ConfigError('gallery_conf["css"] must be list or tuple, got %r'
                          % (gallery_conf['css'],))
    # for css in gallery_conf['css']:
    #     if css not in _KNOWN_CSS:
    #         raise ConfigError('Unknown css %r, must be one of %r'
    #                           % (css, _KNOWN_CSS))
    #     if gallery_conf['app'] is not None:  # can be None in testing
    #         gallery_conf['app'].add_css_file(css + '.css')

    return gallery_conf


def generate_gallery_md(gallery_conf, mkdocs_conf) -> Dict[Path, Tuple[str, Dict[str, str]]]:
    """Generate the Main examples gallery reStructuredText

    Start the mkdocs-gallery configuration and recursively scan the examples
    directories in order to populate the examples gallery

    Returns
    -------
    md_files_toc : Dict[str, Tuple[str, Dict[str, str]]]
        A map of galleries src folders to title and galleries toc (map of title to path)

    md_to_src_file : Dict[str, Path]
        A map of posix absolute file path to generated markdown example -> Path of the src file relative to project root
    """
    logger.info('generating gallery...')  # , color='white')
    # gallery_conf = parse_config(app)  already done

    seen_backrefs = set()
    md_files_toc = dict()
    md_to_src_file = dict()

    # a list of pairs "gallery source" > "gallery dest" dirs
    all_info = AllInformation.from_cfg(gallery_conf, mkdocs_conf)

    # Gather all files except ignored ones, and sort them according to the configuration.
    all_info.collect_script_files()

    # Check for duplicate filenames to make sure linking works as expected
    files = all_info.get_all_script_files()
    check_duplicate_filenames(files)
    check_spaces_in_filenames(files)

    # For each gallery,
    all_results = []
    for gallery in all_info.galleries:
        # Process the root level
        title, root_nested_title, index_md, results = generate(gallery=gallery, seen_backrefs=seen_backrefs)
        write_computation_times(gallery, results)

        # Remember the results so that we can write the final summary
        all_results.extend(results)

        # Fill the md-to-srcfile dict
        md_to_src_file[gallery.index_md_rel_site_root.as_posix()] = gallery.readme_file_rel_project
        for res in results:
            md_to_src_file[res.script.md_file_rel_site_root.as_posix()] = res.script.src_py_file_rel_project

        # Create the toc entries
        root_md_files = {res.script.title: res.script.md_file_rel_site_root.as_posix() for res in results}
        root_md_files = dict_to_list_of_dicts(root_md_files)
        if len(gallery.subsections) == 0:
            # No subsections: do not nest the gallery examples further
            md_files_toc[gallery.generated_dir] = (title, root_md_files)
        else:
            # There are subsections. Find the root gallery title if possible and nest the root contents
            subsection_tocs = [{(root_nested_title or title): root_md_files}]
            md_files_toc[gallery.generated_dir] = (title, subsection_tocs)

        # Create an index.md with all examples
        index_md_new = _new_file(gallery.index_md)
        with codecs.open(str(index_md_new), 'w', encoding='utf-8') as fhindex:
            # Write the README and thumbnails for the root-level examples
            fhindex.write(index_md)

            # If there are any subsections, handle them
            for subg in gallery.subsections:
                # Process the root level
                sub_title, _, sub_index_md, sub_results = generate(gallery=subg, seen_backrefs=seen_backrefs)
                write_computation_times(subg, sub_results)

                # Remember the results so that we can write the final summary
                all_results.extend(sub_results)

                # Fill the md-to-srcfile dict
                for res in sub_results:
                    md_to_src_file[res.script.md_file_rel_site_root.as_posix()] = res.script.src_py_file_rel_project

                # Create the toc entries
                sub_md_files = {res.script.title: res.script.md_file_rel_site_root.as_posix() for res in sub_results}
                sub_md_files = dict_to_list_of_dicts(sub_md_files)
                # Both append the subsection contents to the parent gallery toc
                subsection_tocs.append({sub_title: sub_md_files})
                # ... and also have an independent reference in case the subsection is directly referenced in the nav.
                md_files_toc[subg.generated_dir] = (sub_title, sub_md_files)

                # Write the README and thumbnails for the subgallery examples
                fhindex.write(sub_index_md)

            # Finally generate the download buttons
            if gallery_conf['download_all_examples']:
                download_fhindex = generate_zipfiles(gallery)
                fhindex.write(download_fhindex)

            # And the "generated by..." signature
            if gallery_conf['show_signature']:
                fhindex.write(MKD_GLR_SIG)

        # Remove the .new suffix and update the md5
        index_md = _replace_by_new_if_needed(index_md_new, md5_mode='t')

    _finalize_backreferences(seen_backrefs, all_info)

    if gallery_conf['plot_gallery']:
        logger.info("computation time summary:")  # , color='white')
        lines, lens = _format_for_writing(all_results, kind='console')
        for name, t, m in lines:
            text = ('    - %s:   ' % (name,)).ljust(lens[0] + 10)
            if t is None:
                text += '(not run)'
                logger.info(text)
            else:
                t_float = float(t.split()[0])
                if t_float >= gallery_conf['min_reported_time']:
                    text += t.rjust(lens[1]) + '   ' + m.rjust(lens[2])
                    logger.info(text)

        # Also create a junit.xml file if needed for rep
        if gallery_conf['junit'] and gallery_conf['plot_gallery']:
            write_junit_xml(all_info, all_results)

    return md_files_toc, md_to_src_file


def dict_to_list_of_dicts(dct: Dict) -> List[Dict]:
    """Transform a dict containing several entries into a list of dicts containing one entry each (nav requirement)"""
    return [{k: v} for k, v in dct.items()]


def fill_mkdocs_nav(mkdocs_config: Dict, galleries_tocs: Dict[Path, Tuple[str, Dict[str, str]]]):
    """Creates a new nav by replacing all entries in the nav containing a reference to gallery_index

    Parameters
    ----------
    mkdocs_config

    galleries_tocs : Dict[Path, Tuple[str, Dict[str, str]]]
        A reference dict containing for each gallery, its path (the key) and its title and contents. The
        contents is a dictionary containing title and path to md, for each element in the gallery.
    """
    mkdocs_docs_dir = Path(mkdocs_config["docs_dir"])

    # galleries_tocs_rel = {os.path.relpath(k, mkdocs_config["docs_dir"]): v for k, v in galleries_tocs.items()}
    galleries_tocs_unique = {Path(k).absolute().as_posix(): v for k, v in galleries_tocs.items()}

    def get_gallery_toc(gallery_target_dir_or_index):
        """
        Return (title, gallery_toc) if gallery_target_dir_or_index matches a known gallery,
        or (None, None) otherwise.
        """
        # Do not handle absolute paths
        if os.path.isabs(gallery_target_dir_or_index):
            return None, None, None

        # Auto-remove the "/index.md" if needed
        if gallery_target_dir_or_index.endswith("/index.md"):
            main_toc_entry = gallery_target_dir_or_index
            gallery_target_dir_or_index = gallery_target_dir_or_index[:-9]
        else:
            if gallery_target_dir_or_index.endswith("/"):
                main_toc_entry = gallery_target_dir_or_index + "index.md"
            else:
                main_toc_entry = gallery_target_dir_or_index + "/index.md"

        # Find the actual absolute path for comparison
        gallery_target_dir_or_index = (mkdocs_docs_dir / gallery_target_dir_or_index).absolute().as_posix()

        try:
            title, contents = galleries_tocs_unique[gallery_target_dir_or_index]
        except KeyError:
            # Not a gallery toc
            return None, None, None
        else:
            # A Gallery Toc: fill contents
            return title, main_toc_entry, contents

    def _get_replacement_for(toc_elt, custom_title=None):
        glr_title, main_toc_entry, gallery_toc_entries = get_gallery_toc(toc_elt)
        if custom_title is None:
            custom_title = glr_title
        if gallery_toc_entries is not None:
            # Put the new contents in place
            return {custom_title: [{custom_title: main_toc_entry}] + gallery_toc_entries}
        else:
            # Leave the usual item
            return toc_elt

    def _replace_element(toc_elt):
        if isinstance(toc_elt, str):
            # A single file name directly, e.g. index.md or gallery
            return _get_replacement_for(toc_elt)

        elif isinstance(toc_elt, list):
            # A list of items, either single file_names or one-entry dicts
            return [_replace_element(elt) for elt in toc_elt]

        elif isinstance(toc_elt, dict):
            # A dictionary containing a single element: {title: file_name} of title : (list)
            assert len(toc_elt) == 1  # noqa
            toc_name, toc_elt = tuple(toc_elt.items())[0]

            # Have a look at the element
            if isinstance(toc_elt, str):
                # Special case: this is a gallery with a custom name.
                new_toc_elt = _get_replacement_for(toc_elt, custom_title=toc_name)
                if new_toc_elt is not toc_elt:
                    return new_toc_elt
                else:
                    # not a gallery, return the original contents
                    return {toc_name: toc_elt}
            else:
                # A list: recurse
                return {toc_name: _replace_element(toc_elt)}

        else:
            raise TypeError(f"Unsupported nav item type: f{type(toc_elt)}. Please report this issue to "
                            f"mkdocs-gallery.")

    modded_nav = _replace_element(mkdocs_config["nav"])
    return modded_nav


def _sec_to_readable(t):
    """Convert a number of seconds to a more readable representation."""
    # This will only work for < 1 day execution time
    # And we reserve 2 digits for minutes because presumably
    # there aren't many > 99 minute scripts, but occasionally some
    # > 9 minute ones
    t = datetime(1, 1, 1) + timedelta(seconds=t)
    t = '{0:02d}:{1:02d}.{2:03d}'.format(
        t.hour * 60 + t.minute, t.second,
        int(round(t.microsecond / 1000.)))
    return t


def cost_name_key(result: GalleryScriptResults):
    # sort by descending computation time, descending memory, alphabetical name
    return (-result.exec_time, -result.memory, result.script.src_py_file_rel_project)


def _format_for_writing(results: GalleryScriptResults, kind='md'):
    """Format (name, time, memory) for a single row in the mg_execution_times.md table."""
    lines = list()
    for result in sorted(results, key=cost_name_key):
        if kind == 'md':  # like in mg_execution_times
            text = f"[{result.script.script_stem}](./{result.script.md_file.name}) " \
                   f"({result.script.src_py_file_rel_project.as_posix()})"
            t = _sec_to_readable(result.exec_time)
        else:  # like in generate_gallery
            assert kind == "console"  # noqa
            text = result.script.src_py_file_rel_project.as_posix()
            t = f"{result.exec_time:0.2f} sec"

        # Memory usage
        m = f"{result.memory:.1f} MB"

        # The 3 values in the table : name, time, memory
        lines.append([text, t, m])

    lens = [max(x) for x in zip(*[[len(item) for item in cost] for cost in lines])]
    return lines, lens


def write_computation_times(gallery: GalleryBase, results: List[GalleryScriptResults]):
    """Write the mg_execution_times.md file containing all execution times."""

    total_time = sum(result.exec_time for result in results)
    if total_time == 0:
        return

    target_dir = gallery.generated_dir_rel_site_root
    target_dir_clean = target_dir.as_posix().replace("/", '_')
    # new_ref = 'mkd_glr_%s_mg_execution_times' % target_dir_clean
    with codecs.open(str(gallery.exec_times_md_file), 'w', encoding='utf-8') as fid:
        # Write the header
        fid.write(f"""

# Computation times

**{_sec_to_readable(total_time)}** total execution time for **{target_dir_clean}** files:

""")

        # Write the table of execution times in markdown
        lines, lens = _format_for_writing(results)

        # Create the markdown table.
        # First line of the table  +--------------+
        hline = "".join(('+' + '-' * (length + 2)) for length in lens) + '+\n'
        fid.write(hline)

        # Table rows
        format_str = ''.join('| {%s} ' % (ii,) for ii in range(len(lines[0]))) + '|\n'
        for line in lines:
            line = [ll.ljust(len_) for ll, len_ in zip(line, lens)]
            text = format_str.format(*line)
            assert len(text) == len(hline)  # noqa
            fid.write(text)
            fid.write(hline)


def write_junit_xml(all_info: AllInformation, all_results: List[GalleryScriptResults]):
    """

    Parameters
    ----------
    all_info
    all_results

    Returns
    -------

    """
    gallery_conf = all_info.gallery_conf
    failing_as_expected, failing_unexpectedly, passing_unexpectedly = _parse_failures(gallery_conf)

    n_tests = 0
    n_failures = 0
    n_skips = 0
    elapsed = 0.
    src_dir = all_info.mkdocs_docs_dir
    target_dir = all_info.mkdocs_site_dir
    output = ''
    for result in all_results:
        t = result.exec_time
        fname = result.script.src_py_file_rel_project.as_posix()
        if not any(fname in x for x in (gallery_conf['passing_examples'],
                                        failing_unexpectedly,
                                        failing_as_expected,
                                        passing_unexpectedly)):
            continue  # not subselected by our regex
        title = gallery_conf['titles'][fname]  # use gallery.title

        _cls_name = quoteattr(os.path.splitext(os.path.basename(fname))[0])
        _file = quoteattr(os.path.relpath(fname, src_dir))
        _name = quoteattr(title)

        output += f'<testcase classname={_cls_name!s} file={_file!s} line="1" name={_name!s} time="{t!r}">'
        if fname in failing_as_expected:
            output += '<skipped message="expected example failure"></skipped>'
            n_skips += 1
        elif fname in failing_unexpectedly or fname in passing_unexpectedly:
            if fname in failing_unexpectedly:
                traceback = gallery_conf['failing_examples'][fname]
            else:  # fname in passing_unexpectedly
                traceback = 'Passed even though it was marked to fail'
            n_failures += 1
            _msg = quoteattr(traceback.splitlines()[-1].strip())
            _tb = escape(traceback)
            output += f'<failure message={_msg!s}>{_tb!s}</failure>'
        output += "</testcase>"
        n_tests += 1
        elapsed += t

    # Add the header and footer
    output = f"""<?xml version="1.0" encoding="utf-8"?>
<testsuite errors="0" failures="{n_failures}" name="mkdocs-gallery" skipped="{n_skips}" tests="{n_tests}" time="{elapsed}">
{output}
</testsuite>
"""  # noqa

    # Actually write it at desired file location
    fname = os.path.normpath(os.path.join(target_dir, gallery_conf['junit']))
    junit_dir = os.path.dirname(fname)
    # Make the dirs if needed
    if not os.path.isdir(junit_dir):
        os.makedirs(junit_dir)

    with codecs.open(fname, 'w', encoding='utf-8') as fid:
        fid.write(output)


def touch_empty_backreferences(mkdocs_conf, what, name, obj, options, lines):
    """Generate empty back-reference example files.

    This avoids inclusion errors/warnings if there are no gallery
    examples for a class / module that is being parsed by autodoc"""

    # TODO uncomment below
    return "TODO"
    # if not bool(app.config.mkdocs_gallery_conf['backreferences_dir']):
    #     return
    #
    # examples_path = os.path.join(app.srcdir,
    #                              app.config.mkdocs_gallery_conf[
    #                                  "backreferences_dir"],
    #                              "%s.examples" % name)
    #
    # if not os.path.exists(examples_path):
    #     # touch file
    #     open(examples_path, 'w').close()


def _expected_failing_examples(gallery_conf: Dict, mkdocs_conf: Dict) -> Set[str]:
    """The set of expected failing examples"""
    return set((Path(mkdocs_conf['docs_dir']) / path).as_posix()
               for path in gallery_conf['expected_failing_examples'])


def _parse_failures(gallery_conf: Dict, mkdocs_conf: Dict):
    """Split the failures."""
    failing_examples = set(gallery_conf['failing_examples'].keys())
    expected_failing_examples = _expected_failing_examples(gallery_conf=gallery_conf, mkdocs_conf=mkdocs_conf)

    failing_as_expected = failing_examples.intersection(expected_failing_examples)
    failing_unexpectedly = failing_examples.difference(expected_failing_examples)
    passing_unexpectedly = expected_failing_examples.difference(failing_examples)

    # filter from examples actually run
    passing_unexpectedly = [
        src_file for src_file in passing_unexpectedly
        if re.search(gallery_conf.get('filename_pattern'), src_file)]

    return failing_as_expected, failing_unexpectedly, passing_unexpectedly


def summarize_failing_examples(gallery_conf: Dict, mkdocs_conf: Dict):
    """Collects the list of falling examples and prints them with a traceback.

    Raises ValueError if there where failing examples.
    """
    # if exception is not None:
    #     return

    # Under no-plot Examples are not run so nothing to summarize
    if not gallery_conf['plot_gallery']:
        logger.info('mkdocs-gallery gallery_conf["plot_gallery"] was '
                    'False, so no examples were executed.')  # , color='brown')
        return

    failing_as_expected, failing_unexpectedly, passing_unexpectedly = \
        _parse_failures(gallery_conf=gallery_conf, mkdocs_conf=mkdocs_conf)

    if failing_as_expected:
        logger.info("Examples failing as expected:")  # , color='brown')
        for fail_example in failing_as_expected:
            logger.info('%s failed leaving traceback:', fail_example)   # color='brown')
            logger.info(gallery_conf['failing_examples'][fail_example])  # color='brown')

    fail_msgs = []
    if failing_unexpectedly:
        fail_msgs.append(red("Unexpected failing examples:"))
        for fail_example in failing_unexpectedly:
            fail_msgs.append(f"{fail_example} failed leaving traceback:\n"
                             f"{gallery_conf['failing_examples'][fail_example]}\n")

    if passing_unexpectedly:
        fail_msgs.append(red("Examples expected to fail, but not failing:\n") +
                         "\n".join(passing_unexpectedly) +
                         "\nPlease remove these examples from 'expected_failing_examples' in your mkdocs.yml file."
                         )

    # standard message
    n_good = len(gallery_conf['passing_examples'])
    n_tot = len(gallery_conf['failing_examples']) + n_good
    n_stale = len(gallery_conf['stale_examples'])
    logger.info('\nmkdocs-gallery successfully executed %d out of %d '
                'file%s subselected by:\n\n'
                '    gallery_conf["filename_pattern"] = %r\n'
                '    gallery_conf["ignore_pattern"]   = %r\n'
                '\nafter excluding %d file%s that had previously been run '
                '(based on MD5).\n'
                % (n_good, n_tot, 's' if n_tot != 1 else '',
                   gallery_conf['filename_pattern'],
                   gallery_conf['ignore_pattern'],
                   n_stale, 's' if n_stale != 1 else '',
                   ))  # color='brown')

    if fail_msgs:
        fail_message = ("Here is a summary of the problems encountered "
                        "when running the examples\n\n" +
                        "\n".join(fail_msgs) + "\n" + "-" * 79)
        if gallery_conf['only_warn_on_example_error']:
            logger.warning(fail_message)
        else:
            raise ExtensionError(fail_message)


def check_duplicate_filenames(files: Iterable[Path]):
    """Check for duplicate filenames across gallery directories."""

    used_names = set()
    dup_names = list()

    for this_file in files:
        # this_fname = os.path.basename(this_file)
        if this_file.name in used_names:
            dup_names.append(this_file)
        else:
            used_names.add(this_file.name)

    if len(dup_names) > 0:
        logger.warning(
            'Duplicate example file name(s) found. Having duplicate file '
            'names will break some links. '
            'List of files: {}'.format(sorted(dup_names),))


def check_spaces_in_filenames(files: Iterable[Path]):
    """Check for spaces in filenames across example directories."""
    regex = re.compile(r'[\s]')
    files_with_space = list(filter(regex.search, (str(f) for f in files)))
    if files_with_space:
        logger.warning(
            'Example file name(s) with space(s) found. Having space(s) in '
            'file names will break some links. '
            'List of files: {}'.format(sorted(files_with_space),))


def get_default_config_value(key):
    def default_getter(conf):
        return conf['mkdocs_gallery_conf'].get(key, DEFAULT_GALLERY_CONF[key])
    return default_getter
