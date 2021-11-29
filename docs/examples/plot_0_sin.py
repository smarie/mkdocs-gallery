# -*- coding: utf-8 -*-
"""
Introductory example - Plotting sin
===================================

This is a general example demonstrating a Matplotlib plot output, embedded
Markdown, the use of math notation and cross-linking to other examples. It would be
useful to compare the [source Python file](./plot_0_sin.py) with the
output below.

Source files for gallery examples should start with a triple-quoted header
docstring. Anything before the docstring is ignored by Mkdocs-Gallery and will
not appear in the rendered output, nor will it be executed. This docstring
requires a Markdown header, which is used as the title of the example and
to correctly build cross-referencing links.

Code and embedded Markdown text blocks follow the docstring. The first block
immediately after the docstring is deemed a code block, by default, unless you
specify it to be a text block using a line of ``#``'s or ``#%%`` (see below).
All code blocks get executed by Mkdocs-Gallery and any output, including plots
will be captured. Typically, code and text blocks are interspersed to provide
narrative explanations of what the code is doing or interpretations of code
output.

Mathematical expressions can be included as LaTeX, and will be rendered with
MathJax. See
[mkdocs-material](https://squidfunk.github.io/mkdocs-material/reference/mathjax)
for configuration of your mkdocs.yml as well as for syntax details. For example,
we are about to plot the following function:

$$
x \\rightarrow \\sin(x)
$$

Here the function $\sin$ is evaluated at each point the variable $x$ is defined.
When including LaTeX in a Python string, ensure that you escape the backslashes
or use a raw docstring. You do not need to do this in
text blocks (see below).
"""

import numpy as np
import matplotlib.pyplot as plt

x = np.linspace(0, 2 * np.pi, 100)
y = np.sin(x)

plt.plot(x, y)
plt.xlabel(r'$x$')
plt.ylabel(r'$\sin(x)$')
# To avoid matplotlib text output
plt.show()

#%%
# To include embedded Markdown, use a line of >= 20 ``#``'s or ``#%%`` between
# your Markdown and your code (see [syntax](../../index.md)). This separates your example
# into distinct text and code blocks. You can continue writing code below the
# embedded Markdown text block:

print('This example shows a sin plot!')

#%%
# LaTeX syntax in the text blocks does not require backslashes to be escaped:
#
# $$
# \sin
# $$
#
# Cross referencing
# -----------------
#
# TODO update this part
#
# You can refer to an example from any part of the documentation,
# including from other examples. Mkdocs-Gallery automatically creates reference
# labels for each example. The label consists of the ``.py`` file name,
# prefixed with ``sphx_glr_`` and the name of the
# folder(s) the example is in. Below, the example we want to
# cross-reference is in ``auto_examples`` (the ``gallery_dirs``; see
# :ref:`configure_and_use_sphinx_gallery`), then the subdirectory ``no_output``
# (since the example is within a sub-gallery). The file name of the example is
# ``plot_syntaxerror.py``. We can thus cross-link to the example 'SyntaxError'
# using:
# ``:ref:`sphx_glr_auto_examples_no_output_plot_syntaxerror.py```.
#
# .. seealso::
#     See :ref:`sphx_glr_auto_examples_no_output_plot_syntaxerror.py` for
#     an example with an error.
#
