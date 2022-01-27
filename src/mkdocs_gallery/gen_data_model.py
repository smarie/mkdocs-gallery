#  Authors: Sylvain MARIE <sylvain.marie@se.com>
#            + All contributors to <https://github.com/smarie/mkdocs-gallery>
#
#  Original idea and code: sphinx-gallery, <https://sphinx-gallery.github.io>
#  License: 3-clause BSD, <https://github.com/smarie/mkdocs-gallery/blob/master/LICENSE>
"""
Classes holding information related to gallery examples and exposing derived information, typically paths.
"""

from shutil import copyfile

from abc import abstractmethod, ABC

import re

import os
import stat
import weakref

from typing import List, Dict, Any, Tuple, Union

from pathlib import Path

from .errors import ExtensionError
from .utils import _smart_copy_md5, get_md5sum, _replace_by_new_if_needed, _new_file


def _has_readme(folder: Path) -> bool:
    return _get_readme(folder, raise_error=False) is not None


def _get_readme(dir_: Path, raise_error=True) -> Path:
    """Return the file path for the readme file, if found."""

    assert dir_.is_absolute()  # noqa

    # extensions = ['.txt'] + sorted(gallery_conf['app'].config['source_suffix'])
    extensions = ['.txt'] + ['.md']  # TODO should this be read from mkdocs config ? like above
    for ext in extensions:
        for fname in ('README', 'Readme', 'readme'):
            fpth = dir_ / (fname + ext)
            if fpth.is_file():
                return fpth
    if raise_error:
        raise ExtensionError(
            "Example directory {0} does not have a README/Readme/readme file "
            "with one of the expected file extensions {1}. Please write one to "
            "introduce your gallery.".format(str(dir_), extensions))
    return None


class ImagePathIterator:
    """Iterate over image paths for a given example.

    Parameters
    ----------
    image_path : Path
        The template image path.
    """

    def __init__(self, script: "GalleryScript"):
        self._script = weakref.ref(script)
        self.paths = list()
        self._stop = 1000000

    @property
    def script(self) -> "GalleryScript":
        return self._script()

    def __len__(self):
        """Return the number of image paths already used."""
        return len(self.paths)

    def __iter__(self):
        """Iterate over paths."""
        # we should really never have 1e6, let's prevent some user pain
        for _ii in range(self._stop):
            yield next(self)
        else:
            raise ExtensionError(f"Generated over {self._stop} images")

    # def next(self):
    #     return self.__next__()

    def __next__(self):
        # The +1 here is because we start image numbering at 1 in filenames
        path = self.script.get_image_path(len(self) + 1)
        self.paths.append(path)
        return path


class GalleryScriptResults:
    """Result of running a single gallery file"""
    __slots__ = ("script", "intro", "exec_time", "memory", "thumb")

    def __init__(self, script: "GalleryScript", intro: str, exec_time: float, memory: float, thumb: Path):
        self.script = script
        self.intro = intro
        self.exec_time = exec_time
        self.memory = memory
        self.thumb = thumb

    @property
    def thumb_rel_root_gallery(self) -> Path:
        """The thumbnail path file relative to the root gallery folder (not the subgallery)"""
        return self.thumb.relative_to(self.script.gallery.root.generated_dir)


class ScriptRunVars:
    """The variables created when a script is run."""
    __slots__ = (
        "image_path_iterator", "example_globals", "memory_used_in_blocks", "memory_delta", "fake_main", "stop_executing"
    )

    def __init__(self, image_path_iterator: ImagePathIterator):
        # The iterator returning the next image file paths
        self.image_path_iterator = image_path_iterator

        # The dictionary of globals() for the script
        self.example_globals: Dict[str, Any] = None

        # The memory used along execution (first entry is memory before running the first block)
        self.memory_used_in_blocks: List[float] = None

        # The memory actually used by the code, i.e. the difference between the max used and the memory used before run.
        self.memory_delta: float = None

        # A temporary __main__
        self.fake_main = None

        # A flag that might be set to True if there is an error during execution
        self.stop_executing = False


class GalleryScript:
    """Represents a gallery script and all related files (notebook, md5, etc.)"""

    __slots__ = ("__weakref__", "_gallery", "script_stem", "title", "_py_file_md5", "run_vars")

    def __init__(self, gallery: "GalleryBase", script_src_file: Path):
        self._gallery = weakref.ref(gallery)

        # Make sure the script complies with the gallery
        assert script_src_file.parent == gallery.scripts_dir  # noqa
        assert script_src_file.suffix == ".py"  # noqa

        # Only save the stem
        self.script_stem = script_src_file.stem

        # We do not know the title yet, nor the md5 hash of the script file
        self.title: str = None
        self._py_file_md5: str = None
        self.run_vars: ScriptRunVars = None

    @property
    def gallery(self) -> "GalleryBase":
        """An alias for the gallery hosting this script."""
        return self._gallery()

    @property
    def gallery_conf(self) -> Dict:
        """An alias for the gallery conf"""
        return self.gallery.conf

    @property
    def py_file_name(self) -> str:
        """The script name, e.g. 'my_demo.py'"""
        return f"{self.script_stem}.py"

    @property
    def src_py_file(self) -> Path:
        """The absolute script file path, e.g. <project>/examples/my_script.py"""
        return self.gallery.scripts_dir / self.py_file_name

    @property
    def src_py_file_rel_project(self) -> Path:
        """Return the relative path of script file with respect to the project root, for editing for example."""
        return self.gallery.scripts_dir_rel_project / self.py_file_name

    def is_executable_example(self) -> bool:
        """Tell if this script has to be executed according to gallery configuration: filename_pattern and global plot_gallery

        This can be false for a local module (not matching the filename pattern),
        or if the gallery_conf['plot_gallery'] is set to False to accelerate the build (disabling all executions)

        Returns
        -------
        is_executable_example : bool
            True if script has to be executed
        """
        filename_pattern = self.gallery_conf.get('filename_pattern')
        execute = re.search(filename_pattern, str(self.src_py_file)) and self.gallery_conf['plot_gallery']
        return execute

    @property
    def py_file_md5(self):
        """The md5 checksum of the python script."""
        if self._py_file_md5 is None:
            self._py_file_md5 = get_md5sum(self.src_py_file, mode='t')
        return self._py_file_md5

    @property
    def dwnld_py_file(self) -> Path:
        """The absolute path of the script in the generated gallery dir,e.g. <project>/generated/gallery/my_script.py"""
        return self.gallery.generated_dir / self.py_file_name

    @property
    def dwnld_py_file_rel_site_root(self) -> Path:
        """Return the relative path of script in the generated gallery dir, wrt the mkdocs site root."""
        return self.gallery.generated_dir_rel_site_root / self.py_file_name

    @property
    def codeobj_file(self):
        """The code objects file to use to store example globals"""
        return self.gallery.generated_dir / f"{self.script_stem}_codeobj.pickle"

    def make_dwnld_py_file(self):
        """Copy src file to target file. Use md5 to not overwrite if not necessary. """

        # Use the possibly already computed md5 if available
        md5 = None
        if self.dwnld_py_file.exists():
            md5 = self.py_file_md5

        _smart_copy_md5(src_file=self.src_py_file, dst_file=self.dwnld_py_file, src_md5=md5, md5_mode='t')

    @property
    def ipynb_file(self) -> Path:
        """Return the jupyter notebook file to generate corresponding to the source `script_file`."""
        return self.gallery.generated_dir / f"{self.script_stem}.ipynb"

    @property
    def ipynb_file_rel_site_root(self) -> Path:
        """Return the jupyter notebook file to generate corresponding to the source `script_file`."""
        return self.gallery.generated_dir_rel_site_root / f"{self.script_stem}.ipynb"

    @property
    def md5_file(self):
        """The path of the persisted md5 file written at the end of processing."""
        file = self.dwnld_py_file
        return file.with_name(file.name + '.md5')

    def write_final_md5_file(self):
        """Writes the persisted md5 file."""
        self.md5_file.write_text(self.py_file_md5)

    def has_changed_wrt_persisted_md5(self) -> bool:
        """Check if the source md5 has changed with respect to the persisted .md5 file if any"""

        # Compute the md5 of the src_file if needed
        actual_md5 = self.py_file_md5

        # Grab the already computed md5 if it exists, and compare
        src_md5_file = self.md5_file
        if src_md5_file.exists():
            ref_md5 = src_md5_file.read_text()
            md5_has_changed = (actual_md5 != ref_md5)
        else:
            md5_has_changed = True

        return md5_has_changed

    @property
    def image_name_template(self) -> str:
        """The image file name template for this script file."""
        return "mkd_glr_%s_{0:03}.png" % self.script_stem

    def get_image_path(self, number: int) -> Path:
        """Return the image path corresponding to the given image number, using the template."""
        return self.gallery.images_dir / self.image_name_template.format(number)

    def init_before_processing(self):
        # Make the images dir
        self.gallery.make_images_dir()

        # Init the images iterator
        image_path_iterator = ImagePathIterator(self)

        # Init the structure that will receive the run information.
        self.run_vars = ScriptRunVars(image_path_iterator=image_path_iterator)

    def generate_n_dummy_images(self, img: Path, nb: int):
        """Use 'stock_img' as many times as needed"""
        for _, path in zip(range(nb), self.run_vars.image_path_iterator):
            if not os.path.isfile(path):
                copyfile(str(img), path)

    @property
    def md_file(self) -> Path:
        """Return the markdown file (absolute path) to generate corresponding to the source `script_file`."""
        return self.gallery.generated_dir / f"{self.script_stem}.md"

    @property
    def md_file_rel_root_gallery(self) -> Path:
        """Return the markdown file relative to the root gallery folder of this gallery or subgallery"""
        return self.gallery.subpath / f"{self.script_stem}.md"

    @property
    def md_file_rel_site_root(self) -> Path:
        """Return the markdown file relative to the mkdocs website source root"""
        return self.gallery.generated_dir_rel_site_root / f"{self.script_stem}.md"

    def save_md_example(self, example_md_contents: str):
        """

        Parameters
        ----------
        example_md_contents : str
            The markdown string to save
        """
        # Write to `<py_file_name>.md.new`
        write_file_new = _new_file(self.md_file)
        write_file_new.write_text(example_md_contents, encoding="utf-8")

        # Make it read-only so that people don't try to edit it
        mode = os.stat(write_file_new).st_mode
        ro_mask = 0x777 ^ (stat.S_IWRITE | stat.S_IWGRP | stat.S_IWOTH)
        os.chmod(write_file_new, mode & ro_mask)

        # In case it wasn't in our pattern, only replace the file if it's still stale.
        _replace_by_new_if_needed(write_file_new, md5_mode='t')

    def get_thumbnail_source(self, file_conf) -> Path:
        """Get the path to the image to use as the thumbnail.

        Note that this image will be copied and possibly rescaled later to create the actual thumbnail.

        Parameters
        ----------
        file_conf : dict
            File-specific settings given in source file comments as:
            ``# mkdocs_gallery_<name> = <value>``
        """
        # Read specification of the figure to display as thumbnail from main text
        thumbnail_number = file_conf.get('thumbnail_number', None)
        thumbnail_path = file_conf.get('thumbnail_path', None)

        # thumbnail_number has priority.
        if thumbnail_number is None and thumbnail_path is None:
            # If no number AND no path, set to default thumbnail_number
            thumbnail_number = 1

        if thumbnail_number is not None:
            # Option 1: generate thumbnail from a numbered figure in the script

            if not isinstance(thumbnail_number, int):
                raise ExtensionError(f"mkdocs_gallery_thumbnail_number setting is not a number, got "
                                     f"{thumbnail_number!r}")

            # negative index means counting from the last one
            if thumbnail_number < 0:
                thumbnail_number += len(self.run_vars.image_path_iterator) + 1

            # Generate the image path from the template (not from iterator)
            image_path = self.get_image_path(thumbnail_number)
        else:
            # Option 2: use an existing thumbnail image

            # thumbnail_path is a relative path wrt website root dir
            image_path = self.gallery.all_info.mkdocs_docs_dir / thumbnail_path

        return image_path

    def get_thumbnail_file(self, ext: str) -> Path:
        """Return the thumbnail file to use, for the given image file extension"""
        assert ext[0] == "."  # noqa
        return self.gallery.thumb_dir / ("mkd_glr_%s_thumb%s" % (self.script_stem, ext))


class GalleryBase(ABC):
    """The common part between gallery roots and subsections."""
    __slots__ = ("title", "scripts", "_readme_file")

    @property
    @abstractmethod
    def all_info(self) -> "AllInformation":
        """An alias to the global holder of all information."""

    @property
    @abstractmethod
    def root(self) -> "Gallery":
        """Return the actual root gallery. It may be self or self parent"""

    @property
    @abstractmethod
    def subpath(self) -> Path:
        """Return the subpath for this subgallery. If this is not a subgallery, return `.` """

    @property
    @abstractmethod
    def conf(self) -> Dict:
        """An alias to the global gallery configuration."""

    @property
    @abstractmethod
    def scripts_dir(self) -> Path:
        """"""

    @property
    @abstractmethod
    def scripts_dir_rel_project(self) -> Path:
        """The relative path (wrt project root) where this subgallery scripts are located"""

    @property
    def readme_file(self) -> Path:
        """Return the file path to the readme file, or raise en error if none is found."""
        try:
            return self._readme_file
        except AttributeError:
            self._readme_file = _get_readme(self.scripts_dir)
            return self._readme_file

    @property
    def readme_file_rel_project(self) -> Path:
        """Return the file path to the readme file, relative to the project root."""
        return self.readme_file.relative_to(self.all_info.project_root_dir)

    @property
    def exec_times_md_file(self) -> Path:
        """The absolute path to the execution times markdown file associated with this gallery"""
        return self.generated_dir / 'mg_execution_times.md'

    def is_ignored_script_file(self, f: Path):
        """Return True if file `f` is ignored according to the 'ignore_pattern' configuration."""
        return re.search(self.conf['ignore_pattern'], os.path.normpath(str(f))) is not None

    def collect_script_files(self, apply_ignore_pattern: bool = True, sort_files: bool = True):
        """Collects script files to process in this gallery and sort them according to configuration.

        Parameters
        ----------
        apply_ignore_pattern : bool
            A boolean indicating if the 'ignore_pattern' gallery config option should be applied.

        sort_files : bool
            A boolean indicating if the 'within_subsection_order' gallery config option should be applied.
        """
        assert not hasattr(self, "scripts"), "This can only be called once!"  # noqa

        # get python files
        listdir = list(self.scripts_dir.glob("*.py"))

        # limit which to look at based on regex (similar to filename_pattern)
        if apply_ignore_pattern:
            listdir = [f for f in listdir if not self.is_ignored_script_file(f)]

        # sort them
        if sort_files:
            listdir = sorted(listdir, key=self.conf['within_subsection_order']())

        # Convert to proper objects
        self.scripts: List[GalleryScript] = [GalleryScript(self, f) for f in listdir]

    def get_all_script_files(self) -> List[Path]:
        """Return the list of all script file paths in this (sub)gallery"""
        return [f.src_py_file for f in self.scripts]

    @property
    @abstractmethod
    def generated_dir(self) -> Path:
        """The absolute path where this (sub)gallery will be generated"""

    @property
    @abstractmethod
    def generated_dir_rel_project(self) -> Path:
        """The relative path (wrt project root) where this subgallery will be generated"""

    @property
    @abstractmethod
    def generated_dir_rel_site_root(self) -> Path:
        """The relative path (wrt mkdocs website root, e.g. docs/) where this subgallery will be generated"""

    def make_generated_dir(self):
        """Make sure that the `generated_dir` exists"""
        if not self.generated_dir.exists():
            self.generated_dir.mkdir(parents=True)

    @property
    def images_dir(self) -> Path:
        """The absolute path of the directory where images will be generated."""
        return self.generated_dir / "images"

    def make_images_dir(self):
        """Make sure that the `images_dir` exists and is a folder"""
        if not self.images_dir.exists():
            self.images_dir.mkdir(parents=True)
        else:
            assert self.images_dir.is_dir()  # noqa

    @property
    def thumb_dir(self) -> Path:
        """The absolute path of the directory where image thumbnails will be generated."""
        return self.images_dir / "thumb"

    def make_thumb_dir(self):
        """Make sure that the `thumb_dir` exists and is a folder"""
        if not self.thumb_dir.exists():
            self.thumb_dir.mkdir(parents=True)
        else:
            assert self.thumb_dir.is_dir()  # noqa

    @abstractmethod
    def has_subsections(self) -> bool:
        """Return True if the gallery has at least one subsection"""


class GallerySubSection(GalleryBase):
    """Represents a subsection in a gallery."""
    __slots__ = ("__weakref__", "_parent", "subpath")

    def has_subsections(self) -> bool:
        return False

    def __init__(self, parent: "Gallery", subpath: Path):
        """

        Parameters
        ----------
        parent : Gallery
            The containing Gallery for this sub gallery (subsection)

        subpath : Path
            The path to this subgallery, from its parent gallery. Must be relative.
        """
        assert not subpath.is_absolute()  # noqa
        self.subpath = subpath
        self._parent = weakref.ref(parent)

    @property
    def all_info(self) -> "AllInformation":
        """Alias to access the weak reference"""
        return self.root.all_info

    @property
    def conf(self):
        """An alias to the global gallery configuration."""
        return self.root.conf

    @property
    def root(self) -> "Gallery":
        """Access to the parent gallery through the weak reference."""
        return self._parent()

    @property
    def scripts_dir_rel_project(self):
        """The relative path (wrt project root) where this subgallery scripts are located"""
        return self.root.scripts_dir_rel_project / self.subpath

    @property
    def scripts_dir(self):
        """The absolute path (wrt project root) where this subgallery scripts are located"""
        return self.root.scripts_dir / self.subpath

    @property
    def generated_dir_rel_project(self):
        """The relative path (wrt project root) where this subgallery will be generated"""
        return self.root.generated_dir_rel_project / self.subpath

    @property
    def generated_dir_rel_site_root(self) -> Path:
        """The relative path (wrt mkdocs website root, e.g. docs/) where this subgallery will be generated"""
        return self.root.generated_dir_rel_site_root / self.subpath

    @property
    def generated_dir(self):
        """The absolute path where this subgallery will be generated"""
        return self.root.generated_dir / self.subpath

    def list_downloadable_sources(self) -> List[Path]:
        """Return the list of all .py files in the subgallery generated folder"""
        return list(self.generated_dir.glob("*.py"))


class Gallery(GalleryBase):
    """Represent a root gallery: source path, destination path, etc.

    Subgalleries are attached as a separate member.
    """
    __slots__ = ("__weakref__", "scripts_dir_rel_project", "generated_dir_rel_project", "subsections", "_all_info")

    subpath = Path(".")

    def __init__(self, all_info: "AllInformation", scripts_dir_rel_project: Path, generated_dir_rel_project: Path):
        """

        Parameters
        ----------
        all_info : AllInformation
            The parent structure containing all configurations.

        scripts_dir_rel_project : Path
            The source folder of the current gallery, containing the python files and the readme.md.
            For example ./docs/examples/. It must be relative to the project root.

        generated_dir_rel_project : Path
            The target folder where the documents, notebooks and images from this sub-gallery should be generated.
            For example ./docs/generated/gallery (a subfolder of mkdocs src folder), or
            ./generated/gallery (not a subfolder of mkdocs src folder. TODO explicitly forbid this ?).
            It must be relative to the project root.

        """
        # note: this is the old examples_dir
        scripts_dir_rel_project = Path(scripts_dir_rel_project)
        assert not scripts_dir_rel_project.is_absolute()  # noqa
        self.scripts_dir_rel_project = scripts_dir_rel_project

        # note: this is the old gallery_dir/target_dirsite_root
        generated_dir_rel_project = Path(generated_dir_rel_project)
        assert not generated_dir_rel_project.is_absolute()  # noqa
        self.generated_dir_rel_project = generated_dir_rel_project

        self.subsections: Tuple[GallerySubSection] = None  # type: ignore

        # Make sure the gallery can see all information
        self._attach(all_info=all_info)

        # Check that generated dir is inside docs dir
        if not self.generated_dir.as_posix().startswith(self.all_info.mkdocs_docs_dir.as_posix()):
            raise ValueError("Generated gallery dirs can only be located as subfolders of the mkdocs 'docs_dir'.")

    def has_subsections(self) -> bool:
        return len(self.subsections) > 0

    @property
    def root(self) -> "Gallery":
        """Self is the root of self."""
        return self

    @property
    def scripts_dir(self) -> Path:
        """The folder where python scripts are located, as an absolute path."""
        return self.all_info.project_root_dir / self.scripts_dir_rel_project

    @property
    def index_md(self) -> Path:
        """Path to this root gallery's index markdown page. Note that subgalleries do not have such a page"""
        return self.generated_dir / "index.md"

    @property
    def index_md_rel_site_root(self) -> Path:
        """Path to this root gallery's index markdown page, relative to site root.
        Note that subgalleries do not have such a page"""
        return self.generated_dir_rel_site_root / "index.md"

    @property
    def generated_dir(self) -> Path:
        """The folder where the gallery files will be generated, as an absolute path."""
        return self.all_info.project_root_dir / self.generated_dir_rel_project

    @property
    def generated_dir_rel_site_root(self) -> Path:
        """The folder where the gallery files will be generated, as an absolute path."""
        return self.generated_dir.relative_to(self.all_info.mkdocs_docs_dir)

    def populate_subsections(self):
        """Moved from the legacy `get_subsections`."""

        assert self.subsections is None, "This method can only be called once !"  # noqa

        # List all subfolders with a valid readme
        subfolders = [subfolder for subfolder in self.scripts_dir.iterdir()
                      if subfolder.is_dir() and _has_readme(subfolder)]

        # Sort them
        _sortkey = self.conf['subsection_order']
        sortkey = _sortkey
        if _sortkey is not None:
            def sortkey(subfolder: Path):
                # Apply on the string representation of the folder
                return sortkey(str(subfolder))

        sorted_subfolders = sorted(subfolders, key=sortkey)

        self.subsections = tuple((
            GallerySubSection(self, subpath=f.relative_to(self.scripts_dir))
            for f in sorted_subfolders
        ))

    def collect_script_files(self, recurse: bool = True, apply_ignore_pattern: bool = True, sort_files: bool = True):
        """Collects script files to process in this gallery and sort them according to configuration.

        Parameters
        ----------
        recurse : bool
            If True, this will call collect_script_files on all subsections

        apply_ignore_pattern : bool
            A boolean indicating if the 'ignore_pattern' gallery config option should be applied.

        sort_files : bool
            A boolean indicating if the 'within_subsection_order' gallery config option should be applied.
        """
        # All subsections first
        if recurse:
            for s in self.subsections:
                s.collect_script_files(apply_ignore_pattern=apply_ignore_pattern, sort_files=sort_files)

        # Then the gallery itself
        GalleryBase.collect_script_files(self, apply_ignore_pattern=apply_ignore_pattern, sort_files=sort_files)

    def get_all_script_files(self, recurse=True):
        res = GalleryBase.get_all_script_files(self)
        if recurse:
            for g in self.subsections:
                res += g.get_all_script_files()
        return res

    def _attach(self, all_info: "AllInformation"):
        """Attach a weak reference to the parent object."""
        self._all_info: "AllInformation" = weakref.ref(all_info)  # type: ignore

    @property
    def all_info(self) -> "AllInformation":
        """Alias to access the weak reference"""
        return self._all_info()

    @property
    def conf(self):
        """An alias to the global gallery configuration."""
        return self.all_info.gallery_conf

    def list_downloadable_sources(self, recurse=True) -> List[Path]:
        """Return the list of all .py files in the gallery generated folder"""
        results = list(self.generated_dir.glob("*.py"))
        if recurse:
            for g in self.subsections:
                results += g.list_downloadable_sources()

        return results

    @property
    def zipfile_python(self) -> Path:
        return self.generated_dir / f"{self.generated_dir.name}_python.zip"

    @property
    def zipfile_python_rel_index_md(self) -> Path:
        return Path(f"{self.generated_dir.name}_python.zip")

    @property
    def zipfile_jupyter(self) -> Path:
        return self.generated_dir / f"{self.generated_dir.name}_jupyter.zip"

    @property
    def zipfile_jupyter_rel_index_md(self) -> Path:
        return Path(f"{self.generated_dir.name}_jupyter.zip")


class AllInformation:
    """Represent all galleries as well as the global configuration."""
    __slots__ = ("__weakref__", "galleries", "gallery_conf", "mkdocs_conf", "project_root_dir")

    def __init__(
        self,
        gallery_conf: Dict[str, Any],
        mkdocs_conf: Dict[str, Any],
        project_root_dir: Path,
        gallery_elts: Tuple[Gallery, ...] = ()
    ):
        """

        Parameters
        ----------
        gallery_conf : Dict[str, Any]
            The global mkdocs-gallery config.

        mkdocs_docs_dir : Path
            The 'docs_dir' option in mkdocs.

        mkdocs_site_dir : Path
            The 'site_dir' option in mkdocs

        project_root_dir
        gallery_elts
        """
        self.gallery_conf = gallery_conf

        assert project_root_dir.is_absolute()  # noqa
        self.project_root_dir = project_root_dir

        self.mkdocs_conf = mkdocs_conf

        self.galleries = list(gallery_elts)

    @property
    def mkdocs_docs_dir(self) -> Path:
        return Path(self.mkdocs_conf["docs_dir"])

    @property
    def mkdocs_site_dir(self) -> Path:
        return Path(self.mkdocs_conf["site_dir"])

    def add_gallery(self, scripts_dir: Union[str, Path], generated_dir: Union[str, Path]):
        """Add a gallery to the list of known galleries.

        Parameters
        ----------
        scripts_dir : Union[str, Path]


        generated_dir : Union[str, Path]

        """

        scripts_dir_rel_project = Path(scripts_dir).relative_to(self.project_root_dir)
        generated_dir_rel_project = Path(generated_dir).relative_to(self.project_root_dir)

        # Create the gallery
        g = Gallery(all_info=self, scripts_dir_rel_project=scripts_dir_rel_project,
                    generated_dir_rel_project=generated_dir_rel_project)

        # Add it to the list
        self.galleries.append(g)

    def populate_subsections(self):
        """From the legacy `get_subsections`."""
        for g in self.galleries:
            g.populate_subsections()

    def collect_script_files(
            self, do_subgalleries: bool = True, apply_ignore_pattern: bool = True, sort_files: bool = True
    ):
        """Triggers the files collection in all galleries."""
        for g in self.galleries:
            g.collect_script_files(
                recurse=do_subgalleries, apply_ignore_pattern=apply_ignore_pattern, sort_files=sort_files
            )

    def get_all_script_files(self):
        return [f for g in self.galleries for f in g.get_all_script_files()]

    @property
    def backrefs_dir(self) -> Path:
        """The absolute path to the backreferences dir"""
        return Path(self.gallery_conf['backreferences_dir'])

    def get_backreferences_file(self, module_name) -> Path:
        """Return the path to the backreferences file to use for `module_name` """
        return self.backrefs_dir / f"{module_name}.examples"

    @classmethod
    def from_cfg(self, gallery_conf: Dict, mkdocs_conf: Dict):
        """Factory to create this object from the configuration.

        It creates all galleries and populates their subsections.
        This class method replaces `_prepare_gallery_dirs`.
        """

        # The project root directory
        project_root_dir = Path(mkdocs_conf['config_file_path']).parent
        project_root2 = Path(os.getcwd())
        if project_root2 != project_root_dir:
            raise ValueError("The project root dir is ambiguous ! Please report this issue to mkdocs-gallery.")

        # Create the global object
        all_info = AllInformation(gallery_conf=gallery_conf, mkdocs_conf=mkdocs_conf, project_root_dir=project_root_dir)

        # Source and destination of the galleries
        examples_dirs = gallery_conf['examples_dirs']
        gallery_dirs = gallery_conf['gallery_dirs']

        if not isinstance(examples_dirs, list):
            examples_dirs = [examples_dirs]

        if not isinstance(gallery_dirs, list):
            gallery_dirs = [gallery_dirs]

        # Back references page
        backreferences_dir = gallery_conf['backreferences_dir']
        if backreferences_dir:
            Path(backreferences_dir).mkdir(parents=True, exist_ok=True)

        # Create galleries
        for e_dir, g_dir in zip(examples_dirs, gallery_dirs):
            all_info.add_gallery(scripts_dir=e_dir, generated_dir=g_dir)

        # Scan all subsections
        all_info.populate_subsections()

        return all_info
