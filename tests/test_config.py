from mkdocs_gallery.plugin import GalleryPlugin
from mkdocs.utils import yaml_load


def test_minimal_conf(basic_mkdocs_config):
    """Test that minimal config can be loaded without problem"""

    # Create a mini config
    mini_config = yaml_load("""
examples_dirs: docs/examples          # path to your example scripts
gallery_dirs: docs/generated/gallery  # where to save generated gallery
""")

    # Load it (this triggers validation and default values according to the plugin config schema)
    plugin = GalleryPlugin()
    plugin.load_config(mini_config)

    # Now mimic the on_config event
    result = plugin.on_config(basic_mkdocs_config)

    # See also https://github.com/mkdocs/mkdocs/blob/master/mkdocs/tests/plugin_tests.py
    # And https://github.com/mkdocs/mkdocs/blob/master/mkdocs/tests/search_tests.py

    assert isinstance(plugin.config, dict)
    assert len(plugin.config) > 0
