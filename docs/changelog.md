# Changelog

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
