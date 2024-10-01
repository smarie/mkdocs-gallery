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
    errors, warnings = plugin.load_config(mini_config)

    assert len(errors) == 0
    assert len(warnings) == 0

    # Now mimic the on_config event
    result = plugin.on_config(basic_mkdocs_config)

    # See also https://github.com/mkdocs/mkdocs/blob/master/mkdocs/tests/plugin_tests.py
    # And https://github.com/mkdocs/mkdocs/blob/master/mkdocs/tests/search_tests.py

    assert isinstance(plugin.config, dict)
    assert len(plugin.config) > 0


REPO_ROOT_DIR = Path(__file__).parent.parent


def test_full_conf(basic_mkdocs_config, monkeypatch):
    """Test that full config can be loaded without problem"""

    monkeypatch.chdir(REPO_ROOT_DIR)

    # Create a mini config
    full_config = yaml_load("""
conf_script: docs/gallery_conf.py
examples_dirs:
  - examples
  - docs/tutorials
  # TODO mayavi_examples
gallery_dirs:
  - docs/generated/gallery
  - docs/generated/tutorials
  # TODO tutorials and mayavi_examples

backreferences_dir: docs/generated/backreferences
doc_module: ['mkdocs_gallery', 'numpy']
# reference_url: {sphinx_gallery: None}
image_scrapers: matplotlib
compress_images: ['images', 'thumbnails']
within_subsection_order: FileNameSortKey
expected_failing_examples:
   - examples/no_output/plot_raise.py
   - examples/no_output/plot_syntaxerror.py

# min_reported_time: min_reported_time,  in conf file

binder:
  org: smarie
  repo: mkdocs-gallery
  branch: gh-pages
  binderhub_url: https://mybinder.org
  dependencies: docs/binder_cfg/requirements.txt
  notebooks_dir: notebooks
  use_jupyter_lab: True
show_memory: True
# junit: foo/junit-results.xml
capture_repr: ['_repr_html_', '__repr__']
matplotlib_animations: True
image_srcset: ['2x']
""")

    # Load it (this triggers validation and default values according to the plugin config schema)
    plugin = GalleryPlugin()
    errors, warnings = plugin.load_config(full_config)

    assert len(errors) == 0
    assert len(warnings) == 0

    # Now mimic the on_config event
    result = plugin.on_config(basic_mkdocs_config)

    # See also https://github.com/mkdocs/mkdocs/blob/master/mkdocs/tests/plugin_tests.py
    # And https://github.com/mkdocs/mkdocs/blob/master/mkdocs/tests/search_tests.py

    assert isinstance(plugin.config, dict)
    assert len(plugin.config) > 0
