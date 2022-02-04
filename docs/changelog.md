# Changelog

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
