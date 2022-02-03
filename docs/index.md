# mkdocs-gallery

*[Sphinx-Gallery](https://sphinx-gallery.github.io/) features for [mkdocs](https://www.mkdocs.org/) (no [Sphinx](sphinx-doc.org/) dependency !).*

[![Python versions](https://img.shields.io/pypi/pyversions/mkdocs-gallery.svg)](https://pypi.python.org/pypi/mkdocs-gallery/) [![Build Status](https://github.com/smarie/mkdocs-gallery/actions/workflows/base.yml/badge.svg)](https://github.com/smarie/mkdocs-gallery/actions/workflows/base.yml) [![Tests Status](./reports/junit/junit-badge.svg?dummy=8484744)](./reports/junit/report.html) [![Coverage Status](./reports/coverage/coverage-badge.svg?dummy=8484744)](./reports/coverage/index.html) [![codecov](https://codecov.io/gh/smarie/mkdocs-gallery/branch/main/graph/badge.svg)](https://codecov.io/gh/smarie/mkdocs-gallery) [![Flake8 Status](./reports/flake8/flake8-badge.svg?dummy=8484744)](./reports/flake8/index.html)

[![Documentation](https://img.shields.io/badge/doc-latest-blue.svg)](https://smarie.github.io/mkdocs-gallery/) [![PyPI](https://img.shields.io/pypi/v/mkdocs-gallery.svg)](https://pypi.python.org/pypi/mkdocs-gallery/) [![Downloads](https://pepy.tech/badge/mkdocs-gallery)](https://pepy.tech/project/mkdocs-gallery) [![Downloads per week](https://pepy.tech/badge/mkdocs-gallery/week)](https://pepy.tech/project/mkdocs-gallery) [![GitHub stars](https://img.shields.io/github/stars/smarie/mkdocs-gallery.svg)](https://github.com/smarie/mkdocs-gallery/stargazers) [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.5786851.svg)](https://doi.org/10.5281/zenodo.5786851)

Do you love [Sphinx-Gallery](https://sphinx-gallery.github.io/) but prefer [mkdocs](https://www.mkdocs.org/) over [Sphinx](sphinx-doc.org/) for your documentation ? `mkdocs-gallery` was written for you ;) 

It relies on [mkdocs-material](https://squidfunk.github.io/mkdocs-material) to get the most of mkdocs, so that your galleries look nice !


## Installing

```bash
> pip install mkdocs-gallery
```

## Usage

### 1. Create a source gallery folder

First, create a folder that will contain your gallery examples, for example `docs/examples/`. It will be referenced by the `examples_dirs` [configuration option](#2-configure-mkdocs).

Then in this folder, you may add a readme. This readme should be written in markdown, be named `README` or `readme` or `Readme`, and have a `.md` or `.txt` extension.

Note: the folder can be located inside the usual mkdocs source folder:

```
docs/                    # base mkdocs source directory
└── examples/            # base 'Gallery of Examples' directory
    └── README.md
```

or not

```
examples/            # base 'Gallery of Examples' directory
└── README.md
docs/                # base mkdocs source directory
```

### 2. Configure mkdocs

#### a. Basics

Simply add the following configuration to you `mkdocs.yml`:

```yaml
theme: material    # This theme is mandatory for now, see below

plugins:
  - gallery:
      examples_dirs: docs/examples          # path to your example scripts
      gallery_dirs: docs/generated/gallery  # where to save generated gallery
      # ... (other options)
  
  - search  # make sure the search plugin is still enabled
```

Most [sphinx-gallery configuration options](https://sphinx-gallery.github.io/stable/configuration.html) are supported and can be configured in here after `examples_dirs` and `gallery_dirs`. All paths should be relative to the `mkdocs.yml` file (which is supposed to be located at project root). 

You can look at the configuration used to generate this site as an example: [mkdocs.yml](https://github.com/smarie/mkdocs-gallery/blob/main/mkdocs.yml).

!!! caution
    `mkdocs-gallery` currently requires that you use the `material` theme from `mkdocs-material` to render properly. You may wish to try other themes to see what is missing to support them: actually, only a few things concerning buttons and icons do not seem to currently work properly.

!!! note
    The `search` plugin is not related with mkdocs-gallery. It is activated by default in mkdocs but if you edit the `plugins` configuration you have to add it explicitly again.

Once you've done this, the corresponding gallery will be created the next time you call `mkdocs build` or `mkdocs serve`. However the gallery will not yet appear in the table of contents (mkdocs `nav`). For this you should add the generated gallery to the nav in `mkdocs.yml`:

```yaml
nav:
  - Home: index.md
  - generated/gallery  # This node will automatically be named and have sub-nodes.
```

When the root folder or the root `index.md` of a gallery is added to the nav, it will be automatically populated with sub-nodes for all examples and subgalleries. If you prefer to select examples or subgalleries to include one by one, you may refer to any of them directly in the nav. In that case, no nav automation will be performed - just the usual explicit mkdocs nav.

You may wish to change the gallery's names for display and still benefit from this automation:

```yaml
nav:
  - Home: index.md
  - My Gallery: generated/gallery  # This node will automatically be named and have sub-nodes.
```

See [this site's config](https://github.com/smarie/mkdocs-gallery/blob/main/mkdocs.yml) for an example. See also [mkdocs configuration](https://www.mkdocs.org/user-guide/configuration/) for general information about the `mkdocs.yml` file.

#### b. Advanced

You may wish to use the special `conf_script` option to create the base configuration using a python script, like what was done in Sphinx-gallery:

```yaml
plugins:
  - gallery:
      conf_script: docs/gallery_conf.py
      # ... other options can still be added here
```

The python script should be executable without error, and at the end of execution should contain a `conf` variable defined at the module level. For example this is a valid script:

```python
from mkdocs_gallery.gen_gallery import DefaultResetArgv

conf = {
    'reset_argv': DefaultResetArgv(),
}
```

You can set options both in the script and in the yaml. In case of duplicates, the yaml options override the script-defined ones.

### 3. Add gallery examples

Gallery examples are structured [the same way as in sphinx-gallery](https://sphinx-gallery.github.io/stable/syntax.html), with two major differences: 

 - All comment blocks should be written using **Markdown** instead of rST. 
 - No sphinx directive is supported: all markdown directives should be supported by `mkdocs`, by one of its activated [plugins](https://www.mkdocs.org/dev-guide/plugins/) or by a base markdown extension (see note below).
 - All per-file and per-code block configuration options from sphinx-gallery ([here, bottom](https://sphinx-gallery.github.io/stable/configuration.html?highlight=sphinx_gallery_#list-of-config-options)) are supported, but you have to use the `mkdocs_gallery_[option]` prefix instead of `sphinx_gallery_[options]`.

```
examples/            # base 'Gallery of Examples' directory
├── README.md
├── <.py files>      
└── subgallery_1/     # generates the 'No image output examples' sub-gallery
    ├── README.md
    └── <.py files>
```

### 4. Examples

The entire original [gallery of examples from sphinx-gallery](https://sphinx-gallery.github.io/stable/auto_examples/index.html) is being ported [here](./generated/gallery/) (work in progress). You may wish to check it out in order to see how each technical aspect translates in the mkdocs world.

You can look at the configuration used to generate it here: [mkdocs.yml](https://github.com/smarie/mkdocs-gallery/blob/main/mkdocs.yml).

### 5. Feature Highlights

#### a. Mkdocs "serve" mode

`mkdocs-gallery` supports the mkdocs dev-server `mkdocs serve` so that you can edit your gallery examples with live auto-rebuild (similar to sphinx-autobuild).

As soon as you modify an example file, it will rebuild the documentation and notify your browser. The examples that did not change will be automatically skipped (based on md5, identical to sphinx-gallery).

See [mkdocs documentation](https://www.mkdocs.org/getting-started/) for details.

#### b. Editing Examples

All mkdocs-gallery generated pages have a working "edit page" pencil icon at the top, including gallery summary (readme) pages. This link will take you directly to the source file for easy pull requests on gallery examples !

#### c. Binder

Binder configuration is slightly easier than the one in sphinx-gallery (as of version 1.0.1), as 2 pieces of config are now optional:

 - `branch` (defaults to `"gh-pages"`)
 - `binderhub_url` (defaults to `"https://mybinder.org"`)

### 6. Make your examples shine !

The following `mkdocs` plugins and extensions are automatically activated - you may therefore use them in your markdown blocks without changing your `mkdocs.yml` configuration:

 - [`mkdocs-material`](https://squidfunk.github.io/mkdocs-material) mkdocs plugin: **make sure you check this one out !**
    - [`navigation.indexes`](https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/#section-index-pages) in the `material` theme. This is used for the gallery readme pages to be selectible in the nav without creating an extra entry (see left pane). 
    - [icons + emojis](https://squidfunk.github.io/mkdocs-material/reference/icons-emojis/) :thumbsup: :slight_smile:
    - All no-conf features are there too, for example support for $\LaTeX$ using [Mathjax](https://squidfunk.github.io/mkdocs-material/reference/mathjax/), [code blocks](https://squidfunk.github.io/mkdocs-material/reference/code-blocks/), [Admonitions](https://squidfunk.github.io/mkdocs-material/reference/admonitions/) etc.

 - markdown extensions:
    - [`attr_list`](https://python-markdown.github.io/extensions/attr_list/) to declare attributes such as css classes on markdown elements.
    - [`admonition`](https://python-markdown.github.io/extensions/admonition/) used to add notes.
    - [`pymdownx.details`](https://facelessuser.github.io/pymdown-extensions/extensions/details/) to create foldable notes such as this one.
    - [`pymdownx.highlight`](https://facelessuser.github.io/pymdown-extensions/extensions/highlight/)
    - [`pymdownx.inlinehilite`](https://facelessuser.github.io/pymdown-extensions/extensions/inlinehilite/)
    - [`pymdownx.superfences`](https://facelessuser.github.io/pymdown-extensions/extensions/superfences/)
    - [`pymdownx.snippets`](https://facelessuser.github.io/pymdown-extensions/extensions/snippets/) (Warning: the base path is
      a bit counter-intuitive: it is relative to `cwd`, not to the markdown file ; see the last line of this [tutorial](./generated/tutorials/plot_parse.md))
    - [`pymdownx.emoji`](https://facelessuser.github.io/pymdown-extensions/extensions/emoji/) configured with the catalog from mkdocs-material (see above)


## Citing

If `mkdocs-gallery` helps you with your research work, don't hesitate to spread the word ! For this simply use this Zenodo link [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.5786851.svg)](https://doi.org/10.5281/zenodo.5786851) to get the proper citation entry (at the bottom right of the page, many formats available including BibTeX).

Note: do not hesitate to cite sphinx-gallery too ! [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3741780.svg)](https://doi.org/10.5281/zenodo.3741780)

## See Also

 - [`sphinx-gallery`](https://sphinx-gallery.github.io/)
 - [`mkdocs`](https://www.mkdocs.org/)
 - [`mkdocs-material`](https://squidfunk.github.io/mkdocs-material)
 - [`PyMdown Extensions`](https://facelessuser.github.io/pymdown-extensions/)

### Others

*Do you like this library ? You might also like [smarie's other python libraries](https://github.com/smarie/OVERVIEW#python)* 

## Want to contribute ?

Details on the github page: [https://github.com/smarie/mkdocs-gallery](https://github.com/smarie/mkdocs-gallery)
