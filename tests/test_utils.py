from pathlib import Path
import re
import os
import pytest
from mkdocs_gallery.utils import matches_filepath_pattern


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
