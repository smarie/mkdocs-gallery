# mkdocs-gallery

*[Sphinx-Gallery](https://sphinx-gallery.github.io/) features for [mkdocs](https://www.mkdocs.org/) (no [Sphinx](sphinx-doc.org/) dependency !).*

[![Python versions](https://img.shields.io/pypi/pyversions/mkdocs-gallery.svg)](https://pypi.python.org/pypi/mkdocs-gallery/) [![Build Status](https://github.com/smarie/mkdocs-gallery/actions/workflows/base.yml/badge.svg)](https://github.com/smarie/mkdocs-gallery/actions/workflows/base.yml) [![Tests Status](./reports/junit/junit-badge.svg?dummy=8484744)](./reports/junit/report.html) [![Coverage Status](./reports/coverage/coverage-badge.svg?dummy=8484744)](./reports/coverage/index.html) [![codecov](https://codecov.io/gh/smarie/python-odsclient/branch/main/graph/badge.svg)](https://codecov.io/gh/smarie/python-odsclient) [![Flake8 Status](./reports/flake8/flake8-badge.svg?dummy=8484744)](./reports/flake8/index.html)

[![Documentation](https://img.shields.io/badge/doc-latest-blue.svg)](https://smarie.github.io/mkdocs-gallery/) [![PyPI](https://img.shields.io/pypi/v/mkdocs-gallery.svg)](https://pypi.python.org/pypi/mkdocs-gallery/) [![Downloads](https://pepy.tech/badge/mkdocs-gallery)](https://pepy.tech/project/mkdocs-gallery) [![Downloads per week](https://pepy.tech/badge/mkdocs-gallery/week)](https://pepy.tech/project/mkdocs-gallery) [![GitHub stars](https://img.shields.io/github/stars/smarie/mkdocs-gallery.svg)](https://github.com/smarie/mkdocs-gallery/stargazers)

Do you love [Sphinx-Gallery](https://sphinx-gallery.github.io/) but prefer [mkdocs](https://www.mkdocs.org/) over [Sphinx](sphinx-doc.org/) for your documentation ? `mkdocs-gallery` was written for you ;) 

It relies on [mkdocs-material](https://squidfunk.github.io/mkdocs-material) to get the most of mkdocs, so that your galleries look nice!

## Installing

```bash
> pip install mkdocs-gallery
```

## Usage

### 1. Create a source gallery folder

First, create a folder that will contain your gallery examples, for example `examples/`. It will be referenced by the `examples_dirs` [configuration option](#2-configure-mkdocs). 

In this folder, you may add a readme for now. Note that this readme should be written in markdown, be named `README` or `readme` or `Readme`, and have a `.txt` or `.md` extension.

Note that this folder can be located inside the usual mkdocs source folder:

```
docs/                    # base mkdocs source directory
└── examples/            # base 'Gallery of Examples' directory
    └── README.md
```


### 2. Configure mkdocs

Simply add the following configuration to you `mkdocs.yml`:

```yaml
theme: material

plugins:
  - gallery:
      examples_dirs: docs/examples          # path to your example scripts, relative to mkdocs.yml
      gallery_dirs: docs/generated/gallery  # where to save gallery generated output
      # (other mkdocs-gallry options go here, see https://sphinx-gallery.github.io/stable/configuration.html)
  
  - search  # make sure the search plugin is still enabled
```

Most [sphinx-gallery configuration options](https://sphinx-gallery.github.io/stable/configuration.html) are supported and can be configured in here after `examples_dirs` and `gallery_dirs`.

!!! caution
    `mkdocs-gallery` currently requires that you use the `material` theme from `mkdocs-material` to render prpoperly. You may wish to try other themes to see what is missing to support them: actually, only a few things concerning buttons and icons do not seem to currently work properly.

!!! note
    The `search` plugin is not related with mkdocs-gallery. It is activated by default in mkdocs but if you edit the `plugins` configuration you have to add it explicitly again.

See [mkdocs configuration](https://www.mkdocs.org/user-guide/configuration/) for general information about the `mkdocs.yml` file.

### 3. Add gallery examples

Gallery examples are structured [the same way as in sphinx-gallery](https://sphinx-gallery.github.io/stable/syntax.html), with two major differences: 

 - all comment blocks should be written using markdown instead of rST. 
 - no sphinx directive is supported: all markdown directives should be supported by your mkdocs or one of its plugins.

```
examples/            # base 'Gallery of Examples' directory
├── README.md
├── <.py files>      
└── subgallery_1/     # generates the 'No image output examples' sub-gallery
    ├── README.md
    └── <.py files>
```

### 4. Examples

The entire original [gallery of examples from sphinx-gallery](https://sphinx-gallery.github.io/stable/auto_examples/index.html) has been ported [here](http://127.0.0.1:8000/generated/gallery/). You may wish to check it out in order to see how each technical aspect translates in the mkdocs world.


## See Also

 - [`mkdocs`](mkdocs.org/)
 - [`mkdocs-material`](https://squidfunk.github.io/mkdocs-material)
 - [`sphinx-gallery`](https://sphinx-gallery.github.io/)

### Others

*Do you like this library ? You might also like [smarie's other python libraries](https://github.com/smarie/OVERVIEW#python)* 

## Want to contribute ?

Details on the github page: [https://github.com/smarie/mkdocs-gallery](https://github.com/smarie/mkdocs-gallery)
