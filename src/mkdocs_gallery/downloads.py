#  Authors: Sylvain MARIE <sylvain.marie@se.com>
#            + All contributors to <https://github.com/smarie/mkdocs-gallery>
#
#  Original idea and code: sphinx-gallery, <https://sphinx-gallery.github.io>
#  License: 3-clause BSD, <https://github.com/smarie/mkdocs-gallery/blob/master/LICENSE>
"""
Utilities for downloadable items
"""

from __future__ import absolute_import, division, print_function

from pathlib import Path

from typing import List

from zipfile import ZipFile
from .gen_data_model import Gallery

from .utils import _replace_by_new_if_needed, _new_file


def python_zip(file_list: List[Path], gallery: Gallery, extension='.py'):
    """Stores all files in file_list with modified extension `extension` into an zip file

    Parameters
    ----------
    file_list : List[Path]
        Holds all the files to be included in zip file. Note that if extension
        is set to

    gallery : Gallery
        gallery for which to create the zip file

    extension : str
        The replacement extension for files in file_list. '.py' or '.ipynb'.
        In order to deal with downloads of python sources and jupyter notebooks,
        since we know that there is one notebook for each python file.

    Returns
    -------
    zipfile : Path
        zip file, written as `<target_dir>_{python,jupyter}.zip` depending on the extension
    """
    zipfile = gallery.zipfile_python if extension == '.py' else gallery.zipfile_jupyter

    # Create the new zip
    zipfile_new = _new_file(zipfile)
    with ZipFile(str(zipfile_new), mode='w') as zipf:
        for file in file_list:
            file_src = file.with_suffix(extension)
            zipf.write(file_src, file_src.relative_to(gallery.generated_dir))

    # Replace the old one if needed
    _replace_by_new_if_needed(zipfile_new)

    return zipfile


def generate_zipfiles(gallery: Gallery):
    """
    Collects all Python source files and Jupyter notebooks in
    gallery_dir and makes zipfiles of them

    Parameters
    ----------
    gallery : Gallery
        path of the gallery to collect downloadable sources

    Return
    ------
    download_md: str
        Markdown to include download buttons to the generated files
    """
    # Collect the files to include in the zip
    listdir = gallery.list_downloadable_sources(recurse=True)

    # Create the two zip files
    python_zip(listdir, gallery, extension=".py")
    python_zip(listdir, gallery, extension=".ipynb")

    icon = ":fontawesome-solid-download:"
    dw_md = f"""
<div id="download_links"></div>

[{icon} Download all examples in Python source code: {gallery.zipfile_python.name}](./{gallery.zipfile_python_rel_index_md}){{ .md-button .center}}

[{icon} Download all examples in Jupyter notebooks: {gallery.zipfile_jupyter.name}](./{gallery.zipfile_jupyter_rel_index_md}){{ .md-button .center}}
"""  # noqa
    return dw_md
