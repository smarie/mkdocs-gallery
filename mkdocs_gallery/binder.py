#  Authors: Sylvain MARIE <sylvain.marie@se.com>
#            + All contributors to <https://github.com/smarie/mkdocs-gallery>
#
#  Original idea and code: sphinx-gallery, <https://sphinx-gallery.github.io>
#  License: 3-clause BSD, <https://github.com/smarie/mkdocs-gallery/blob/master/LICENSE>
"""
Binder utility functions
"""
from pathlib import Path

from tqdm import tqdm

import os
import shutil
from urllib.parse import quote

from typing import Dict

from .errors import ConfigError
from .gen_data_model import GalleryScript
from . import mkdocs_compatibility, glr_path_static

logger = mkdocs_compatibility.getLogger('mkdocs-gallery')


def gen_binder_url(script: GalleryScript, binder_conf):
    """Generate a Binder URL according to the configuration in conf.py.

    Parameters
    ----------
    script: GalleryScript
        The script for which a Binder badge will be generated.
    binder_conf: dict or None
        The Binder configuration dictionary. See `gen_binder_md` for details.

    Returns
    -------
    binder_url : str
        A URL that can be used to direct the user to the live Binder environment.
    """
    # Build the URL
    fpath_prefix = binder_conf.get('filepath_prefix')
    link_base = binder_conf.get('notebooks_dir')

    # We want to keep the relative path to sub-folders
    path_link = os.path.join(link_base, script.ipynb_file_rel_site_root.as_posix())

    # In case our website is hosted in a sub-folder
    if fpath_prefix is not None:
        path_link = '/'.join([fpath_prefix.strip('/'), path_link])

    # Make sure we have the right slashes (in case we're on Windows)
    path_link = path_link.replace(os.path.sep, '/')

    # Create the URL
    # See https://mybinder.org/ to check that it is still the right one
    # Note: the branch will typically be gh-pages
    binder_url = '/'.join([binder_conf['binderhub_url'],
                           'v2', 'gh',
                           binder_conf['org'],
                           binder_conf['repo'],
                           quote(binder_conf['branch'])])

    if binder_conf.get('use_jupyter_lab', False) is True:
        binder_url += '?urlpath=lab/tree/{}'.format(quote(path_link))
    else:
        binder_url += '?filepath={}'.format(quote(path_link))
    return binder_url


def gen_binder_md(script: GalleryScript, binder_conf: Dict):
    """Generate the MD + link for the Binder badge.

    Parameters
    ----------
    script: GalleryScript
        The script for which a Binder badge will be generated.

    binder_conf: dict or None
        If a dictionary it must have the following keys:

        'binderhub_url'
            The URL of the BinderHub instance that's running a Binder service.
        'org'
            The GitHub organization to which the documentation will be pushed.
        'repo'
            The GitHub repository to which the documentation will be pushed.
        'branch'
            The Git branch on which the documentation exists (e.g., gh-pages).
        'dependencies'
            A list of paths to dependency files that match the Binderspec.

    Returns
    -------
    md : str
        The Markdown for the Binder badge that links to this file.
    """
    binder_url = gen_binder_url(script, binder_conf)

    # TODO revisit this comment for mkdocs
    # In theory we should be able to use glr_path_static for this, but Sphinx only allows paths to be relative to the
    # build root. On Linux, absolute paths can be used and they work, but this does not seem to be
    # documented behavior: https://github.com/sphinx-doc/sphinx/issues/7772
    # And in any case, it does not work on Windows, so here we copy the SVG to `images` for each gallery and link to it
    # there. This will make a few copies, and there will be an extra in `_static` at the end of the build, but it at
    # least works...
    physical_path = script.gallery.images_dir / "binder_badge_logo.svg"
    if not physical_path.exists():
        # Make sure parent dirs exists (this should not be necessary actually)
        physical_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(os.path.join(glr_path_static(), 'binder_badge_logo.svg'), str(physical_path))
    else:
        assert physical_path.is_file()  # noqa

    # Create the markdown image with a link
    return f"[![Launch binder](./images/binder_badge_logo.svg)]({binder_url}){{ .center}}"


def copy_binder_files(gallery_conf, mkdocs_conf):
    """Copy all Binder requirements and notebooks files."""
    # if exception is not None:
    #     return
    #
    # if app.builder.name not in ['html', 'readthedocs']:
    #     return

    # gallery_conf = app.config.sphinx_gallery_conf
    binder_conf = gallery_conf['binder']

    if not len(binder_conf) > 0:
        return

    logger.info('copying binder requirements...')  # , color='white')
    _copy_binder_reqs(binder_conf, mkdocs_conf)
    _copy_binder_notebooks(gallery_conf, mkdocs_conf)


def _copy_binder_reqs(binder_conf, mkdocs_conf):
    """Copy Binder requirements files to a ".binder" folder in the docs.

    See https://mybinder.readthedocs.io/en/latest/using/config_files.html#config-files
    """
    path_reqs = binder_conf.get('dependencies')

    # Check that they exist (redundant since the check is already done by mkdocs.)
    for path in path_reqs:
        if not os.path.exists(path):
            raise ConfigError(f"Couldn't find the Binder requirements file: {path}, did you specify it correctly?")

    # Destination folder: a ".binder" folder
    binder_folder = os.path.join(mkdocs_conf['site_dir'], '.binder')
    if not os.path.isdir(binder_folder):
        os.makedirs(binder_folder)

    # Copy over the requirement files to the output directory
    for path in path_reqs:
        shutil.copy(path, binder_folder)


def _remove_ipynb_files(path, contents):
    """Given a list of files in `contents`, remove all files named `ipynb` or
    directories named `images` and return the result.

    Used with the `shutil` "ignore" keyword to filter out non-ipynb files."""
    contents_return = []
    for entry in contents:
        if entry.endswith('.ipynb'):
            # Don't include ipynb files
            pass
        elif (entry != "images") and os.path.isdir(os.path.join(path, entry)):
            # Don't include folders not called "images"
            pass
        else:
            # Keep everything else
            contents_return.append(entry)
    return contents_return


def _copy_binder_notebooks(gallery_conf, mkdocs_conf):
    """Copy Jupyter notebooks to the binder notebooks directory.

    Copy each output gallery directory structure but only including the
    Jupyter notebook files."""

    gallery_dirs = gallery_conf.get('gallery_dirs')
    binder_conf = gallery_conf.get('binder')
    notebooks_dir = os.path.join(mkdocs_conf['site_dir'], binder_conf.get('notebooks_dir'))
    shutil.rmtree(notebooks_dir, ignore_errors=True)
    os.makedirs(notebooks_dir)

    if not isinstance(gallery_dirs, (list, tuple)):
        gallery_dirs = [gallery_dirs]

    for gallery_dir in tqdm(gallery_dirs, desc=f"copying binder notebooks... "):
        gallery_dir_rel_docs_dir = Path(gallery_dir).relative_to(mkdocs_conf['docs_dir'])
        shutil.copytree(gallery_dir, os.path.join(notebooks_dir, gallery_dir_rel_docs_dir), ignore=_remove_ipynb_files)


def check_binder_conf(binder_conf):
    """Check to make sure that the Binder configuration is correct."""

    # Grab the configuration and return None if it's not configured
    binder_conf = {} if binder_conf is None else binder_conf
    if not isinstance(binder_conf, dict):
        raise ConfigError('`binder_conf` must be a dictionary or None.')
    if len(binder_conf) == 0:
        return binder_conf

    # Ensure all fields are populated
    req_values = ['binderhub_url', 'org', 'repo', 'branch', 'dependencies']
    optional_values = ['filepath_prefix', 'notebooks_dir', 'use_jupyter_lab']
    missing_values = []
    for val in req_values:
        if binder_conf.get(val) is None:
            missing_values.append(val)

    if len(missing_values) > 0:
        raise ConfigError(f"binder_conf is missing values for: {missing_values}")

    for key in binder_conf.keys():
        if key not in (req_values + optional_values):
            raise ConfigError(f"Unknown Binder config key: {key}")

    # Ensure we have http in the URL
    if not any(binder_conf['binderhub_url'].startswith(ii) for ii in ['http://', 'https://']):
        raise ConfigError(f"did not supply a valid url, gave binderhub_url: {binder_conf['binderhub_url']}")

    # Ensure we have at least one dependency file
    # Need at least one of these three files
    required_reqs_files = ['requirements.txt', 'environment.yml', 'Dockerfile']

    path_reqs = binder_conf['dependencies']
    if isinstance(path_reqs, str):
        path_reqs = [path_reqs]
        binder_conf['dependencies'] = path_reqs
    elif not isinstance(path_reqs, (list, tuple)):
        raise ConfigError(f"`dependencies` value should be a list of strings. Got type {type(path_reqs)}.")

    binder_conf['notebooks_dir'] = binder_conf.get('notebooks_dir', 'notebooks')

    path_reqs_filenames = [os.path.basename(ii) for ii in path_reqs]
    if not any(ii in path_reqs_filenames for ii in required_reqs_files):
        raise ConfigError("Did not find one of `requirements.txt` or `environment.yml` in the \"dependencies\" section"
                          " of the binder configuration for mkdocs-gallery. A path to at least one of these files must"
                          " exist in your Binder dependencies.")

    return binder_conf
