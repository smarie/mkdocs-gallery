from pathlib import Path
import re
import os
import pytest
from mkdocs_gallery.utils import matches_filepath_pattern, is_relative_to


class TestFilepathPatternMatch:
    FILEPATH = Path("/directory/filename.ext")

    @pytest.mark.parametrize("pattern", [
        r"filename",
        r"filename\.ext",
        r"\.ext",
        re.escape(os.sep) + r"filename",
        r"directory",
        re.escape(os.sep) + r"directory",
    ])
    def test_ok(self, pattern):
        """Test that the pattern matches the filename"""

        assert matches_filepath_pattern(TestFilepathPatternMatch.FILEPATH, pattern)

    @pytest.mark.parametrize("pattern", [
        r"wrong_filename",
        r"wrong_filename\.ext",
        r"\.wrong_ext",
        re.escape(os.sep) + r"wrong_filename",
        r"wrong_directory",
        re.escape(os.sep) + r"wrong_directory",
    ])
    def test_fails(self, pattern):
        """Test that the pattern does not match the filename"""

        assert not matches_filepath_pattern(TestFilepathPatternMatch.FILEPATH, pattern)

    def test_not_path_raises(self):
        """Test that the function raises an exception when filepath is not a Path object"""

        filepath = str(TestFilepathPatternMatch.FILEPATH)
        pattern = r"filename"

        with pytest.raises(AssertionError):
            matches_filepath_pattern(filepath, pattern)


class TestRelativePaths:

    @pytest.mark.parametrize(
        "path1, path2, expected", [
            ("parent", "parent/sub", True),
            ("notparent", "parent/sub", False),
        ])
    def test_behavior(self, path1, path2, expected):
        """Test that the function behaves as expected"""

        assert is_relative_to(Path(path1), Path(path2)) == expected

    @pytest.mark.parametrize(
        "path1, path2", [
            ("parent", "parent/sub"),
            (Path("parent"), "parent/sub"),
            ("parent", Path("parent/sub")),
        ])
    def test_not_paths_raises(self, path1, path2):
        """Test that the function raises an exception when both arguments are not Path objects"""

        with pytest.raises(TypeError):
            is_relative_to(path1, path2)
