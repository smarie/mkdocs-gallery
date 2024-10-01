import pytest

from mkdocs.config import load_config


@pytest.fixture(scope="session")
def tmp_root_dir(tmp_path_factory):
    """A temporary directory that gets used as the mkdocs root dir"""

    root_dir = tmp_path_factory.mktemp("mkdg-test")

    yield root_dir


@pytest.fixture
def basic_mkdocs_config(tmp_root_dir):
    """A basic mkdocs config"""

    docs_dir = tmp_root_dir / "docs"
    examples_dir = docs_dir / "examples"
    examples_dir.mkdir(parents=True)
    tmp_cfg_file = tmp_root_dir / "mkdocs.yml"

    # contents of the config file
    tmp_cfg_file.write_text('\n'.join([
        'site_name: basic_conf',
    ]
    ))

    yield load_config(str(tmp_cfg_file))


