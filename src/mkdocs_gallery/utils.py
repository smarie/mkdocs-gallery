#  Authors: Sylvain MARIE <sylvain.marie@se.com>
#            + All contributors to <https://github.com/smarie/mkdocs-gallery>
#
#  Original idea and code: sphinx-gallery, <https://sphinx-gallery.github.io>
#  License: 3-clause BSD, <https://github.com/smarie/mkdocs-gallery/blob/master/LICENSE>
"""
Utilities
=========

Miscellaneous utilities.
"""

from __future__ import division, absolute_import, print_function

import hashlib
import os
from pathlib import Path
from shutil import move, copyfile
import subprocess
from typing import Tuple

from . import mkdocs_compatibility
from .errors import ExtensionError

logger = mkdocs_compatibility.getLogger('mkdocs-gallery')


def _get_image():
    try:
        from PIL import Image
    except ImportError as exc:  # capture the error for the modern way
        try:
            import Image
        except ImportError:
            raise ExtensionError(
                'Could not import pillow, which is required '
                'to rescale images (e.g., for thumbnails): %s' % (exc,))
    return Image


def rescale_image(in_file: Path, out_file: Path, max_width, max_height):
    """Scales an image with the same aspect ratio centered in an
       image box with the given max_width and max_height
       if in_file == out_file the image can only be scaled down
    """
    # local import to avoid testing dependency on PIL:
    Image = _get_image()
    img = Image.open(in_file)
    # XXX someday we should just try img.thumbnail((max_width, max_height)) ...
    width_in, height_in = img.size
    scale_w = max_width / float(width_in)
    scale_h = max_height / float(height_in)

    if height_in * scale_w <= max_height:
        scale = scale_w
    else:
        scale = scale_h

    if scale >= 1.0 and in_file.absolute().as_posix() == out_file.absolute().as_posix():
        # do not proceed: the image can only be scaled down.
        return

    width_sc = int(round(scale * width_in))
    height_sc = int(round(scale * height_in))

    # resize the image using resize; if using .thumbnail and the image is
    # already smaller than max_width, max_height, then this won't scale up
    # at all (maybe could be an option someday...)
    img = img.resize((width_sc, height_sc), Image.BICUBIC)
    # img.thumbnail((width_sc, height_sc), Image.BICUBIC)
    # width_sc, height_sc = img.size  # necessary if using thumbnail

    # insert centered
    thumb = Image.new('RGBA', (max_width, max_height), (255, 255, 255, 0))
    pos_insert = ((max_width - width_sc) // 2, (max_height - height_sc) // 2)
    thumb.paste(img, pos_insert)

    try:
        thumb.save(out_file)
    except IOError:
        # try again, without the alpha channel (e.g., for JPEG)
        thumb.convert('RGB').save(out_file)


def optipng(file: Path, args=()):
    """Optimize a PNG in place.

    Parameters
    ----------
    file : Path
        The file. If it ends with '.png', ``optipng -o7 fname`` will
        be run. If it fails because the ``optipng`` executable is not found
        or optipng fails, the function returns.
    args : tuple
        Extra command-line arguments, such as ``['-o7']``.
    """
    if file.suffix == '.png':
        # -o7 because this is what CPython used
        # https://github.com/python/cpython/pull/8032
        fname = file.as_posix()
        try:
            subprocess.check_call(
                ['optipng'] + list(args) + [fname],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        except (subprocess.CalledProcessError, IOError):  # FileNotFoundError
            pass
    else:
        raise ValueError(f"File extension is not .png: {file}")


def _has_optipng():
    try:
        subprocess.check_call(['optipng', '--version'],
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
    except IOError:  # FileNotFoundError
        return False
    else:
        return True


def replace_ext(file: Path, new_ext: str, expected_ext: str = None) -> Path:
    """Replace the extension in `file` with `new_ext`, with optional initial `expected_ext` check.

    Parameters
    ----------
    file : Path
        the file path.

    new_ext : str
        The new extension, e.g. '.ipynb'

    expected_ext : str
        The expected original extension for checking, if provided.

    Returns
    -------
    new_file : Path
        The same file with a different ext.
    """
    # Optional extension checking
    if expected_ext is not None and file.suffix != expected_ext:
        raise ValueError(f"Unrecognized file extension, expected {expected_ext}, got {file.suffix}")

    # Replace extension
    return file.with_suffix(new_ext)


def get_md5sum(src_file: Path, mode='b'):
    """Returns md5sum of file

    Parameters
    ----------
    src_file : str
        Filename to get md5sum for.
    mode : 't' or 'b'
        File mode to open file with. When in text mode, universal line endings
        are used to ensure consitency in hashes between platforms.
    """
    errors = 'surrogateescape' if mode == 't' else None
    with open(str(src_file), 'r' + mode, errors=errors) as src_data:
        src_content = src_data.read()
        if mode == 't':
            src_content = src_content.encode(errors=errors)
        return hashlib.md5(src_content).hexdigest()


def _get_old_file(new_file: Path) -> Path:
    """Return the same file without the .new suffix"""
    assert new_file.name.endswith('.new')  # noqa
    return new_file.with_name(new_file.stem)  # this removes the .new suffix


def _have_same_md5(file_a, file_b, mode: str = 'b') -> bool:
    """Return `True` if both files have the same md5, computed using `mode`."""
    return get_md5sum(file_a, mode) == get_md5sum(file_b, mode)


def _smart_move_md5(src_file: Path, dst_file: Path, md5_mode: str = 'b'):
    """Move `src_file` to `dst_file`, overwriting `dst_file` only if md5 has changed.

    Parameters
    ----------
    src_file : Path
        The source file path.

    dst_file : Path
        The destination file path.

    md5_mode : str
        A string representing the md5 computation mode, 'b' or 't'
    """
    assert src_file.is_absolute() and dst_file.is_absolute()  # noqa
    assert src_file != dst_file  # noqa

    if dst_file.exists() and _have_same_md5(dst_file, src_file, mode=md5_mode):
        # Shortcut: destination is already identical, just delete the source
        os.remove(src_file)
    else:
        # Proceed to the move operation
        move(str(src_file), dst_file)
        assert dst_file.exists()  # noqa

    return dst_file


def _new_file(file: Path) -> Path:
    """Return the same file path with a .new additional extension."""
    return file.with_suffix(f"{file.suffix}.new")


def _replace_by_new_if_needed(file_new: Path, md5_mode: str = 'b'):
    """Use `file_new` (suffix .new) instead of the old file (same path but no suffix).

    If the new file is identical to the old one, the old one will not be touched.

    Parameters
    ----------
    file_new : Path
        The new file, ending with .new suffix.

    md5_mode : str
        A string representing the md5 computation mode, 'b' or 't'
    """
    _smart_move_md5(src_file=file_new, dst_file=_get_old_file(file_new), md5_mode=md5_mode)


def _smart_copy_md5(src_file: Path, dst_file: Path, src_md5: str = None, md5_mode: str = 'b') -> Tuple[Path, str]:
    """Copy `src_file` to `dst_file`, overwriting `dst_file`, only if md5 has changed.

    Parameters
    ----------
    src_file : Path
        The source file path.

    dst_file : Path
        The destination file path.

    src_md5 : str
        If the source md5 was already computed, users may provide it here to avoid computing it again.

    md5_mode : str
        A string representing the md5 computation mode, 'b' or 't'

    Returns
    -------
    md5 : str
        The md5 of the file, if it has been provided or computed in the process, or None.
    """
    assert src_file.is_absolute() and dst_file.is_absolute()  # noqa
    assert src_file != dst_file  # noqa

    if dst_file.exists():
        if src_md5 is None:
            src_md5 = get_md5sum(src_file, mode=md5_mode)

        dst_md5 = get_md5sum(dst_file, mode=md5_mode)
        if src_md5 == dst_md5:
            # Shortcut: nothing to do
            return src_md5

    # Proceed to the copy operation
    copyfile(src_file, dst_file)
    assert dst_file.exists()  # noqa

    return src_md5


# def check_md5sum_changed(src_file: Path, src_md5: str = None, md5_mode='b') -> Tuple[bool, str]:
#     """Checks whether src_file has the same md5 hash as the one on disk on not
#
#     Legacy name: md5sum_is_current
#
#     Parameters
#     ----------
#     src_file : Path
#         The file to check
#
#     md5_mode : str
#         The md5 computation mode
#
#     Returns
#     -------
#     md5_has_changed : bool
#         A boolean indicating if src_file has changed with respect
#
#     actual_md5 : str
#         The actual md5 of src_file
#     """
#
#     # Compute the md5 of the src_file
#     actual_md5 = get_md5sum(src_file, mode=mode)
#
#     # Grab the already computed md5 if it exists, and compare
#     src_md5_file = src_file.with_name(src_file.name + '.md5')
#     if src_md5_file.exists():
#         ref_md5 = src_md5_file.read_text()
#         md5_has_changed = (actual_md5 != ref_md5)
#     else:
#         md5_has_changed = True
#
#     return md5_has_changed, actual_md5


class Bunch(dict):
    """Dictionary-like object that exposes its keys as attributes."""

    def __init__(self, **kwargs):  # noqa: D102
        dict.__init__(self, kwargs)
        self.__dict__ = self


def _has_pypandoc():
    """Check if pypandoc package available."""
    try:
        import pypandoc  # noqa
        # Import error raised only when function called
        version = pypandoc.get_pandoc_version()
    except (ImportError, OSError):
        return None, None
    else:
        return True, version
