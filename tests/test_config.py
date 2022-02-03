import pytest
from pathlib import Path

from mkdocs.config import load_config
from mkdocs_gallery.plugin import GalleryPlugin
from mkdocs.utils import yaml_load


@pytest.fixture
def tmp_root_dir(tmpdir):
    """A temporary directory that gets set as the current working dir during the test using it"""
    with tmpdir.as_cwd() as _old_cwd:
        yield Path(str(tmpdir))


@pytest.fixture
def basic_mkdocs_config(tmp_root_dir):
    """A basic mkdocs config"""

    docs_dir = tmp_root_dir / "docs"
    examples_dir = docs_dir / "examples"
    examples_dir.mkdir(parents=True)
    tmp_cfg_file = tmp_root_dir / "mkdocs.yml"

    # contents of the config file
    tmp_cfg_file.write_text("""
site_name: basic_conf
""")

    yield load_config(str(tmp_cfg_file))


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
