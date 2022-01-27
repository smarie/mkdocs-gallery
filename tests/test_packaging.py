import pkg_resources


def test_packaged_static():
    """Test that the static resources can be found in the package."""
    binder_badge = pkg_resources.resource_string("mkdocs_gallery", "static/binder_badge_logo.svg").decode("utf-8")
    assert binder_badge.startswith("<svg")
