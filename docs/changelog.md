# Changelog

### 0.10.2 - Bugfixes

- **SECURITY** removed insecure polyfill extra javascript from example. Fixes [#99](https://github.com/smarie/mkdocs-gallery/issues/99).
- Fixed dead link at the bottom of the generated gallery examples. Fixes [#97](https://github.com/smarie/mkdocs-gallery/issues/97).
- Fixed compliance issue with `mkdocs-material`'s [metadata declaration feature](https://squidfunk.github.io/mkdocs-material/reference/#usage). Fixes [#96](https://github.com/smarie/mkdocs-gallery/issues/96).

### 0.10.1 - More flexible gallery folders

- `examples` folder is not required to be in a subfolder of `docs` anymore. Fixes [#54](https://github.com/smarie/mkdocs-gallery/issues/54). PR [#92](https://github.com/smarie/mkdocs-gallery/pull/92) by [Louis-Pujol](https://github.com/Louis-Pujol).

### 0.10.0 - Support for asynchronous code

- Gallery scripts now support top-level asynchronous code. PR [#90](https://github.com/smarie/mkdocs-gallery/pull/90) by [pmeier](https://github.com/pmeier)

### 0.9.0 - Pyvista

- Pyvista can now be used in gallery examples as in `sphinx-gallery`. PR [#91](https://github.com/smarie/mkdocs-gallery/pull/91) by [Louis-Pujol](https://github.com/Louis-Pujol)

### 0.8.0 - Mayavi

 - Mayavi can now be used in gallery examples just as in `sphinx-gallery`. PR [#69](https://github.com/smarie/mkdocs-gallery/pull/69) by [GenevieveBuckley](https://github.com/GenevieveBuckley)
 - Fixed for `README.md` that contains `html` comments. Fixes [#85](https://github.com/smarie/mkdocs-gallery/issues/85). PR [#86](https://github.com/smarie/mkdocs-gallery/pull/86) by [AntoineD](https://github.com/AntoineD).

### 0.7.10 - `sys.path` is not reset between code blocks

 - `sys.path` modifications now persist across blocks of an example. `sys.path` is still reset after each example. PR [#82](https://github.com/smarie/mkdocs-gallery/pull/82) by [Louis-Pujol](https://github.com/Louis-Pujol).

### 0.7.9 - `optipng` and better error messages

 - Fixed `AttributeError` when `optipng` is installed and used through the `compress_images` option. PR [#77](https://github.com/smarie/mkdocs-gallery/pull/77) by [Samreay](https://github.com/Samreay)
 - Swapped from deprecated `disutils.version` to `packaging.version`. PR [#79](https://github.com/smarie/mkdocs-gallery/pull/79) by [Samreay](https://github.com/Samreay)
 - Re-raise errors for better ExtensionError messages, so users have full details about the original problem. PR [#58](https://github.com/smarie/mkdocs-gallery/pull/58) by [GenevieveBuckley](https://github.com/GenevieveBuckley)

### 0.7.8 - Bugfixes

 - Fixed `Plugin 'gallery' option 'binder': Sub-option 'org': Required configuration not provided.`. Fixes [#62](https://github.com/smarie/mkdocs-gallery/issues/62)
 - Support relative path to `mkdocs.yaml` file using `--config-file` option. Fixes [#63](https://github.com/smarie/mkdocs-gallery/issues/63). PR [#64](https://github.com/smarie/mkdocs-gallery/pull/64) by [fgrbr](https://github.com/fgrbr).

### 0.7.7 - Bugfixes and new python versions

 - Official support for python 3.10 and 3.11. PR [#52](https://github.com/smarie/mkdocs-gallery/pull/52) by [GenevieveBuckley](https://github.com/GenevieveBuckley)
 - Fixed `AttributeError: MySubConfig has no '_pre_validate'` with `mkdocs` version `1.4` or greater. Fixes [#57](https://github.com/smarie/mkdocs-gallery/issues/57)

### 0.7.6 - Bugfixes

 - Fixed incorrect img `srcset` paths leading to figures not being displayed in gallery examples. Fixes [#47](https://github.com/smarie/mkdocs-gallery/issues/47)
 - Fixed `TypeError: startswith first arg must be str or a tuple of str, not WindowsPath` when running with `mkdocs serve`. Fixes [#45](https://github.com/smarie/mkdocs-gallery/issues/45). PR [#46](https://github.com/smarie/mkdocs-gallery/pull/46) by [mchaaler](https://github.com/mchaaler).

### 0.7.5 - Bugfixes

 - Examples expected to fail are now correctly skipped in case of identical md5 hash, too. Fixes [#34](https://github.com/smarie/mkdocs-gallery/issues/34). PR [#39](https://github.com/smarie/mkdocs-gallery/pull/39) by [mchaaler](https://github.com/mchaaler).

### 0.7.4 - Bugfixes

 - Python scripts are now correctly skipped in case of identical md5 hash. Fixes [#29](https://github.com/smarie/mkdocs-gallery/issues/29). PR [#27](https://github.com/smarie/mkdocs-gallery/pull/27) by [mchaaler](https://github.com/mchaaler).
 - Fixed error when `edit_url` is set to empty to [disable the "edit page" feature](https://www.mkdocs.org/user-guide/configuration/#edit_uri). Fixes [#32](https://github.com/smarie/mkdocs-gallery/issues/32). PR [#27](https://github.com/smarie/mkdocs-gallery/pull/27) by [mchaaler](https://github.com/mchaaler).

This release was yanked because of [#34](https://github.com/smarie/mkdocs-gallery/issues/34).

### 0.7.3 - Bugfix

 - `matplotlib` was still not optional by default because of the associated `image_scraper` that was called even when not used. It is now truly optional. Fixed [#24](https://github.com/smarie/mkdocs-gallery/issues/24)

### 0.7.2 - Misc. bug fixes and improvements

 - Fixed `KeyError` issue when using a minimalistic configuration. Fixed [#22](https://github.com/smarie/mkdocs-gallery/issues/22).
 - `matplotlib` is now optional. Fixed [#24](https://github.com/smarie/mkdocs-gallery/issues/24)

### 0.7.1 - Packaging is now correct

 - Fixed packaging issue: static resources were not included in wheel. Adopted `src/` layout. Fixed [#19](https://github.com/smarie/mkdocs-gallery/issues/19).

### 0.7.0 - Code output max height + updated one example

 - Code output now have a correct height limit. Fixed [#7](https://github.com/smarie/mkdocs-gallery/issues/7)
 - Fixed the "Notebook Style Example" tutorial. Fixed [#17](https://github.com/smarie/mkdocs-gallery/issues/17)

### 0.6.0 - All examples + Edit page link + Binder badges !

 - Completed the gallery of examples. Fixed [#1](https://github.com/smarie/mkdocs-gallery/issues/1)
 - Fixed HTML repr (example 2, typically used to display pandas tables). Fixed [#11](https://github.com/smarie/mkdocs-gallery/issues/11)
 - Binder badges now work correctly. Fixes [#5](https://github.com/smarie/mkdocs-gallery/issues/5)
 - "Edit page" links (pencil icon at the top) now work as expected: they take the user to the source python file used to generate the page. It also works for gallery readme pages ! Fixes [#8](https://github.com/smarie/mkdocs-gallery/issues/8)
 - backreferences files are now written but it is still not clear how they should be used in a mkdocs context, see [#10](https://github.com/smarie/mkdocs-gallery/issues/10)
 - Fixed most flake8 issues and warnings.

### 0.5.0 - First public working release

Initial release with:

 - Basic features:
   - pages generation with markdown-based gallery examples. Currently only the `material` theme renders correctly
   - download buttons (both on each example and on the summaries) and page header link to the downloads section
   - subgalleries
   - gallery synthesis with proper icons and subgalleries
   - auto inclusion in the ToC (nav) with support for the [section index pages feature](https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/#section-index-pages)
   - working `mkdocs serve`: correctly ignoring generated files to avoid infinite build loop
   - working `mkdocs.yml` configuration for most options
   - New option `conf_script` to configure via a script as in Sphinx-gallery.

 - All gallery examples from Sphinx-Gallery successfully translated, in particular:
   - LaTeX support works

 - Refactoring:
   - Using pathlib all over the place
   - Using f-string whenever possible
   - Object-oriented approach for configuration and dir/file names used in the generated files.
