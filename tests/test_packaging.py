from pathlib import Path

import pkg_resources

from mkdocs_gallery import glr_path_static
from mkdocs_gallery.scrapers import _find_image_ext


def test_packaged_static():
    """Test that the static resources can be found in the package."""
    binder_badge = pkg_resources.resource_string("mkdocs_gallery", "static/binder_badge_logo.svg").decode("utf-8")
    assert binder_badge.startswith("<svg")

    thumb_source_path = Path(glr_path_static()) / 'broken_example.png'
    thumb_image_path, ext = _find_image_ext(thumb_source_path)
    assert ext == ".png"
