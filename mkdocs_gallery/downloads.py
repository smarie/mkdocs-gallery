# -*- coding: utf-8 -*-
r"""
Utilities for downloadable items
================================

"""
# Author: Óscar Nájera
# License: 3-clause BSD

from __future__ import absolute_import, division, print_function

import os
import zipfile

from .utils import _replace_md5

# TODO what about only html > remove binder badge?
CODE_DOWNLOAD = """
<div id="download_links"></div>

{binder_badge_md}

[{download_icon} Download Python source code: {py_name}](./{py_name}){{ .md-button }}

[{download_icon} Download Jupyter notebook: {ipynb_name}](./{ipynb_name}){{ .md-button }}
"""

CODE_ZIP_DOWNLOAD = """
<div id="download_links"></div>

[{download_icon} Download all examples in Python source code: {py_name}](./{py_zip}){{ .md-button }}

[{download_icon} Download all examples in Jupyter notebooks: {ipynb_name}](./{ipynb_zip}){{ .md-button }}
"""


def python_zip(file_list, gallery_path, extension='.py'):
    """Stores all files in file_list into an zip file

    Parameters
    ----------
    file_list : list
        Holds all the file names to be included in zip file
    gallery_path : str
        path to where the zipfile is stored
    extension : str
        '.py' or '.ipynb' In order to deal with downloads of python
        sources and jupyter notebooks the file extension from files in
        file_list will be removed and replace with the value of this
        variable while generating the zip file
    Returns
    -------
    zipname : str
        zip file name, written as `target_dir_{python,jupyter}.zip`
        depending on the extension
    """
    zipname = os.path.basename(os.path.normpath(gallery_path))
    zipname += '_python' if extension == '.py' else '_jupyter'
    zipname = os.path.join(gallery_path, zipname + '.zip')
    zipname_new = zipname + '.new'
    with zipfile.ZipFile(zipname_new, mode='w') as zipf:
        for fname in file_list:
            file_src = os.path.splitext(fname)[0] + extension
            zipf.write(file_src, os.path.relpath(file_src, gallery_path))
    _replace_md5(zipname_new)
    return zipname


def list_downloadable_sources(target_dir):
    """Returns a list of python source files is target_dir

    Parameters
    ----------
    target_dir : str
        path to the directory where python source file are
    Returns
    -------
    list
        list of paths to all Python source files in `target_dir`
    """
    return [os.path.join(target_dir, fname)
            for fname in os.listdir(target_dir)
            if fname.endswith('.py')]


def generate_zipfiles(gallery_dir, src_dir):
    """
    Collects all Python source files and Jupyter notebooks in
    gallery_dir and makes zipfiles of them

    Parameters
    ----------
    gallery_dir : str
        path of the gallery to collect downloadable sources
    src_dir : str
        The build source directory. Needed to make the RST paths relative.

    Return
    ------
    download_md: str
        Markdown to include download buttons to the generated files
    """
    # Collect the files to include in the zip
    listdir = list_downloadable_sources(gallery_dir)
    for directory in sorted(os.listdir(gallery_dir)):
        if os.path.isdir(os.path.join(gallery_dir, directory)):
            target_dir = os.path.join(gallery_dir, directory)
            listdir.extend(list_downloadable_sources(target_dir))
    # Create the two zip files
    py_zipfile = python_zip(listdir, gallery_dir)
    jy_zipfile = python_zip(listdir, gallery_dir, ".ipynb")

    def md_path(filepath):
        filepath = os.path.relpath(filepath, gallery_dir) #os.path.normpath(src_dir))
        return filepath.replace(os.sep, '/')

    py_name = os.path.basename(py_zipfile)
    ipynb_name = os.path.basename(jy_zipfile)
    icon = ":fontawesome-solid-download:"
    dw_md = CODE_ZIP_DOWNLOAD.format(py_name=py_name, download_icon=icon,
                                     py_zip=md_path(py_zipfile),
                                     ipynb_name=ipynb_name,
                                     ipynb_zip=md_path(jy_zipfile))
    return dw_md
