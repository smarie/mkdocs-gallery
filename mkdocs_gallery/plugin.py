from pathlib import Path

from mkdocs.config.base import ValidationError
from mkdocs.config import config_options as co
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import Files

from typing import Dict, Any

import os

from . import glr_path_static
from .binder import copy_binder_files
# from .docs_resolv import embed_code_links
from .gen_gallery import parse_config, _KNOWN_CSS, generate_gallery_md, summarize_failing_examples, fill_mkdocs_nav


class ConfigList(co.OptionallyRequired):
    """A list or single element of configuration matching a specific ConfigOption"""

    def __init__(self, item_config: co.BaseConfigOption, single_elt_allowed: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.single_elt_allowed = single_elt_allowed
        self.item_config = item_config

    def run_validation(self, value):
        if not isinstance(value, (list, tuple)):
            if self.single_elt_allowed:
                value = (value, )
            else:
                msg = f"Expected a list but received a single element."
                raise ValidationError(msg)

        # Validate all elements in the list
        result = []
        for i, v in enumerate(value):
            try:
                result.append(self.item_config.validate(v))
            except ValidationError as e:
                raise ValidationError(f"Error validating config item #{i+1}: {e}")
        return result


class MySubConfig(co.SubConfig):
    """Same as SubConfig except that it will be an empty dict when nothing is provided by user,
    instead of a dict with all options containing their default values."""

    def validate(self, value):
        if value is None or len(value) == 0:
            return None
        else:
            return super(MySubConfig, self).validate(value)


class GalleryPlugin(BasePlugin):
    #     # Mandatory to display plotly graph within the site
    #     import plotly.io as pio
    #     pio.renderers.default = "sphinx_gallery"

    config_scheme = (
        ('conf_script', co.File(exists=True)),
        ('filename_pattern', co.Type(str)),
        ('ignore_pattern', co.Type(str)),
        ('examples_dirs', ConfigList(co.Dir(exists=True))),
        # 'reset_argv': DefaultResetArgv(),
        ('subsection_order', co.Choice(choices=(None, "ExplicitOrder"))),
        ('within_subsection_order', co.Choice(choices=("FileNameSortKey", "NumberOfCodeLinesSortKey"))),

        ('gallery_dirs', ConfigList(co.Dir(exists=False))),
        ('backreferences_dir', co.Dir(exists=False)),
        ('doc_module', ConfigList(co.Type(str))),
        # 'reference_url': {},  TODO how to link code to external functions?
        ('capture_repr', ConfigList(co.Type(str))),
        ('ignore_repr_types', co.Type(str)),
        # Build options
        ('plot_gallery', co.Type(bool)),
        ('download_all_examples', co.Type(bool)),
        ('abort_on_example_error', co.Type(bool)),
        ('only_warn_on_example_error', co.Type(bool)),
        # 'failing_examples': {},  # type: Set[str]
        # 'passing_examples': [],
        # 'stale_examples': [],
        ('run_stale_examples', co.Type(bool)),
        ('expected_failing_examples', ConfigList(co.File(exists=True))),
        ('thumbnail_size', ConfigList(co.Type(int), single_elt_allowed=False)),
        ('min_reported_time', co.Type(int)),
        ('binder', MySubConfig(
            # Required keys
            ('org', co.Type(str, required=True)),
            ('repo', co.Type(str, required=True)),
            ('branch', co.Type(str, required=True)),
            ('binderhub_url', co.URL(required=True)),
            ('dependencies', ConfigList(co.File(exists=True), required=True)),
            # Optional keys
            ('filepath_prefix', co.Type(str)),
            ('notebooks_dir', co.Type(str)),
            ('use_jupyter_lab', co.Type(bool)),
        )),
        ('image_scrapers', ConfigList(co.Type(str))),
        ('compress_images', ConfigList(co.Type(str))),
        ('reset_modules', ConfigList(co.Type(str))),
        ('first_notebook_cell', co.Type(str)),
        ('last_notebook_cell', co.Type(str)),
        ('notebook_images', co.Type(bool)),
        # # 'pypandoc': False,
        ('remove_config_comments', co.Type(bool)),
        ('show_memory', co.Type(bool)),
        ('show_signature', co.Type(bool)),
        # 'junit': '',
        # 'log_level': {'backreference_missing': 'warning'},
        ('inspect_global_variables', co.Type(bool)),
        # 'css': _KNOWN_CSS,
        ('matplotlib_animations', co.Type(bool)),
        ('image_srcset', ConfigList(co.Type(str))),
        ('default_thumb_file', co.File(exists=True)),
        ('line_numbers', co.Type(bool)),
    )

    def on_config(self, config, **kwargs):
        """
        TODO Add plugin templates and scripts to config.
        """

        from mkdocs.utils import yaml_load

        # Enable navigation indexes in "material" theme,
        # see https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/#section-index-pages
        if config["theme"].name == "material":
            if "navigation.indexes" not in config["theme"]["features"]:
                if "toc.integrate" not in config["theme"]["features"]:
                    config["theme"]["features"].append("navigation.indexes")

        extra_config_yml = """
markdown_extensions:
  # to declare attributes such as css classes on markdown elements. For example to change the color
  - attr_list

  # to add notes such as http://squidfunk.github.io/mkdocs-material/extensions/admonition/
  - admonition

  # to display the code blocks https://squidfunk.github.io/mkdocs-material/reference/code-blocks/
  - pymdownx.highlight
  - pymdownx.inlinehilite
  - pymdownx.details
  - pymdownx.superfences
  - pymdownx.snippets

  # to have the download icons in the buttons
  - pymdownx.emoji:
      emoji_index: !!python/name:materialx.emoji.twemoji
      emoji_generator: !!python/name:materialx.emoji.to_svg


"""
        extra_config = yaml_load(extra_config_yml)
        merge_extra_config(extra_config, config)

        # Append static resources
        static_resources_dir = glr_path_static()
        config['theme'].dirs.append(static_resources_dir)
        for css_file in os.listdir(static_resources_dir):
            if css_file.endswith(".css"):
                config['extra_css'].append(css_file)
        # config['theme'].static_templates.add('search.html')
        # config['extra_javascript'].append('search/main.js')

        # Use the sphinx-gallery config validator (almost)
        # TODO move to an object-oriented version of the config ?
        self.config = parse_config(self.config, mkdocs_conf=config)

        # TODO do we need to register those CSS files and how ? (they are already registered ads
        # for css in self.config['css']:
        #     if css not in _KNOWN_CSS:
        #         raise ConfigError('Unknown css %r, must be one of %r'
        #                           % (css, _KNOWN_CSS))
        #     if gallery_conf['app'] is not None:  # can be None in testing
        #         gallery_conf['app'].add_css_file(css + '.css')

        return config

    def on_pre_build(self, config, **kwargs):
        """Create one md file for each python example in the gallery, and update the navigation."""

        # TODO ?
        #   if 'sphinx.ext.autodoc' in app.extensions:
        #       app.connect('autodoc-process-docstring', touch_empty_backreferences)
        #   app.add_directive('minigallery', MiniGallery)
        #   app.add_directive("image-sg", ImageSg)
        #   imagesg_addnode(app)

        galleries_tocs = generate_gallery_md(self.config, config)

        # Update the nav for all galleries if needed
        new_nav = fill_mkdocs_nav(config, galleries_tocs)
        config["nav"] = new_nav

    def on_files(self, files, config):
        """Remove the md files from the gallery"""

        # Get the list of gallery source files, possibly containing the readme.md that we wish to exclude
        gallery_conf = self.config
        examples_dirs = gallery_conf['examples_dirs']
        if not isinstance(examples_dirs, list):
            examples_dirs = [examples_dirs]
        # Get them relative to the mkdocs source dir
        mkdocs_src_dir = config['docs_dir']
        examples_dirs = [os.path.relpath(e, mkdocs_src_dir) for e in examples_dirs]

        def exclude(i):
            i_path = Path(i.src_path)
            for d in examples_dirs:
                if i_path.match(f"^{d}/**/*") or i_path.match(f"^{d}/*"):
                    return True
            return False

        out = []
        for i in files:
            if not exclude(i):
                out.append(i)

        return Files(out)

    # def on_nav(self, nav, config, files):
    #     # Nav already modded in on_pre_build
    #     return nav

    # def on_page_content(self, html, page: Page, config: Config, files: Files):
    #     """Edit the 'edit this page' link, see https://github.com/oprypin/mkdocs-gen-files/blob/master/mkdocs_gen_files/plugin.py"""
    #
    #     # TODO
    #     repo_url = config.get("repo_url", None)
    #     edit_uri = config.get("edit_uri", None)
    #
    #     if page.file.src_path in self._edit_paths:
    #         path = self._edit_paths.pop(page.file.src_path)
    #         if repo_url and edit_uri:
    #             page.edit_url = path and urllib.parse.urljoin(
    #                 urllib.parse.urljoin(repo_url, edit_uri), path
    #             )
    #
    #     return html

    def on_serve(self, server, config, builder):
        """"""

        # self.observer.schedule(handler, path, recursive=recursive)
        excluded_dirs = self.config["gallery_dirs"]
        if isinstance(excluded_dirs, str):
            excluded_dirs = [excluded_dirs]  # a single dir

        def wrap_callback(original_callback):
            def _callback(event):
                for g in excluded_dirs:
                    # TODO maybe use fnmatch rather ?
                    if event.src_path.startswith(g):
                        # ignore this event: the file is in the gallery target dir.
                        # log.info(f"Ignoring event: {event}")
                        return
                return original_callback(event)
            return _callback

        # TODO this is an ugly hack...
        # Find the objects in charge of monitoring the dirs and modify their callbacks
        for watch, handlers in server.observer._handlers.items():
            for h in handlers:
                h.on_any_event = wrap_callback(h.on_any_event)

        return server

    def on_post_build(self, config, **kwargs):
        """Create one md file for each python example in the gallery."""

        # TODO copy_binder_files(gallery_conf=self.config, mkdocs_conf=config)
        summarize_failing_examples(gallery_conf=self.config, mkdocs_conf=config)
        # TODO embed_code_links()


def merge_extra_config(extra_config: Dict[str, Any], config):
    """Extend the configuration 'markdown_extensions' list with extension_name if needed."""

    for extension_cfg in extra_config["markdown_extensions"]:
        if isinstance(extension_cfg, str):
            extension_name = extension_cfg
            if extension_name not in config['markdown_extensions']:
                config['markdown_extensions'].append(extension_name)
        elif isinstance(extension_cfg, dict):
            assert len(extension_cfg) == 1
            extension_name, extension_options = extension_cfg.popitem()
            if extension_name not in config['markdown_extensions']:
                config['markdown_extensions'].append(extension_name)
            if extension_name not in config['mdx_configs']:
                config['mdx_configs'][extension_name] = extension_options
            else:
                # Only add options that are not already set
                # TODO should we warn ?
                for cfg_key, cfg_val in extension_options.items():
                    if cfg_key not in config['mdx_configs'][extension_name]:
                        config['mdx_configs'][extension_name][cfg_key] = cfg_val
        else:
            raise TypeError(extension_cfg)


# class SearchPlugin(BasePlugin):
#     """ Add a search feature to MkDocs. """
#
#     config_scheme = (
#         ('lang', LangOption()),
#         ('separator', co.Type(str, default=r'[\s\-]+')),
#         ('min_search_length', co.Type(int, default=3)),
#         ('prebuild_index', co.Choice((False, True, 'node', 'python'), default=False)),
#         ('indexing', co.Choice(('full', 'sections', 'titles'), default='full'))
#     )
#
#     def on_config(self, config, **kwargs):
#         "Add plugin templates and scripts to config."
#         if 'include_search_page' in config['theme'] and config['theme']['include_search_page']:
#             config['theme'].static_templates.add('search.html')
#         if not ('search_index_only' in config['theme'] and config['theme']['search_index_only']):
#             path = os.path.join(base_path, 'templates')
#             config['theme'].dirs.append(path)
#             if 'search/main.js' not in config['extra_javascript']:
#                 config['extra_javascript'].append('search/main.js')
#         if self.config['lang'] is None:
#             # lang setting undefined. Set default based on theme locale
#             validate = self.config_scheme[0][1].run_validation
#             self.config['lang'] = validate(config['theme']['locale'].language)
#         # The `python` method of `prebuild_index` is pending deprecation as of version 1.2.
#         # TODO: Raise a deprecation warning in a future release (1.3?).
#         if self.config['prebuild_index'] == 'python':
#             log.info(
#                 "The 'python' method of the search plugin's 'prebuild_index' config option "
#                 "is pending deprecation and will not be supported in a future release."
#             )
#         return config
#
#     def on_page_context(self, context, **kwargs):
#         "Add page to search index."
#         self.search_index.add_entry_from_context(context['page'])
#
#     def on_post_build(self, config, **kwargs):
#         "Build search index."
#         output_base_path = os.path.join(config['site_dir'], 'search')
#         search_index = self.search_index.generate_search_index()
#         json_output_path = os.path.join(output_base_path, 'search_index.json')
#         utils.write_file(search_index.encode('utf-8'), json_output_path)
#
#         if not ('search_index_only' in config['theme'] and config['theme']['search_index_only']):
#             # Include language support files in output. Copy them directly
#             # so that only the needed files are included.
#             files = []
#             if len(self.config['lang']) > 1 or 'en' not in self.config['lang']:
#                 files.append('lunr.stemmer.support.js')
#             if len(self.config['lang']) > 1:
#                 files.append('lunr.multi.js')
#             if ('ja' in self.config['lang'] or 'jp' in self.config['lang']):
#                 files.append('tinyseg.js')
#             for lang in self.config['lang']:
#                 if (lang != 'en'):
#                     files.append(f'lunr.{lang}.js')
#
#             for filename in files:
#                 from_path = os.path.join(base_path, 'lunr-language', filename)
#                 to_path = os.path.join(output_base_path, filename)
#                 utils.copy_file(from_path, to_path)
