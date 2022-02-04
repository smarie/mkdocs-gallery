#  Authors: Sylvain MARIE <sylvain.marie@se.com>
#            + All contributors to <https://github.com/smarie/mkdocs-gallery>
#
#  Original idea and code: sphinx-gallery, <https://sphinx-gallery.github.io>
#  License: 3-clause BSD, <https://github.com/smarie/mkdocs-gallery/blob/master/LICENSE>
"""
Scrapers for embedding images
=============================

Collect images that have been produced by code blocks.

The only scrapers we support are Matplotlib and Mayavi, others should
live in modules that will support them (e.g., PyVista, Plotly).  Scraped
images are injected as rst ``image-sg`` directives into the ``.md``
file generated for each example script.
"""

from typing import Dict, Optional, List

import os
import sys
import re
from distutils.version import LooseVersion
from textwrap import indent
from pathlib import PurePosixPath, Path
from warnings import filterwarnings

from .errors import ExtensionError

from .gen_data_model import GalleryScript
from .utils import rescale_image, optipng

__all__ = ['save_figures', 'figure_md_or_html', 'clean_modules', 'matplotlib_scraper', 'mayavi_scraper']


###############################################################################
# Scrapers

def _import_matplotlib():
    """Import matplotlib safely."""
    # make sure that the Agg backend is set before importing any
    # matplotlib
    import matplotlib
    matplotlib.use('agg')
    matplotlib_backend = matplotlib.get_backend().lower()

    filterwarnings("ignore", category=UserWarning,
                   message='Matplotlib is currently using agg, which is a'
                           ' non-GUI backend, so cannot show the figure.')

    if matplotlib_backend != 'agg':
        raise ExtensionError(
            "mkdocs-gallery relies on the matplotlib 'agg' backend to "
            "render figures and write them to files. You are "
            "currently using the {} backend. mkdocs-gallery will "
            "terminate the build now, because changing backends is "
            "not well supported by matplotlib. We advise you to move "
            "mkdocs_gallery imports before any matplotlib-dependent "
            "import. Moving mkdocs_gallery imports at the top of "
            "your conf.py file should fix this issue"
            .format(matplotlib_backend))

    import matplotlib.pyplot as plt
    return matplotlib, plt


def _matplotlib_fig_titles(fig):
    titles = []
    # get supertitle if exists
    suptitle = getattr(fig, "_suptitle", None)
    if suptitle is not None:
        titles.append(suptitle.get_text())
    # get titles from all axes, for all locs
    title_locs = ['left', 'center', 'right']
    for ax in fig.axes:
        for loc in title_locs:
            text = ax.get_title(loc=loc)
            if text:
                titles.append(text)
    fig_titles = ', '.join(titles)
    return fig_titles


_ANIMATION_RST = """
<div class="mkd-glr-animation">
{html}
</div>
"""


def matplotlib_scraper(block, script: GalleryScript, **kwargs):
    """Scrape Matplotlib images.

    Parameters
    ----------
    block : tuple
        A tuple containing the (label, content, line_number) of the block.

    script : GalleryScript
        Dict of block variables.

    **kwargs : dict
        Additional keyword arguments to pass to
        :meth:`~matplotlib.figure.Figure.savefig`, e.g. ``format='svg'``.
        The ``format`` kwarg in particular is used to set the file extension
        of the output file (currently only 'png', 'jpg', and 'svg' are
        supported).

    Returns
    -------
    md : str
        The Markdown that will be rendered to HTML containing
        the images. This is often produced by :func:`figure_md_or_html`.
    """
    try:
        matplotlib, plt = _import_matplotlib()
    except ImportError:
        # Matplotlib is not installed. Ignore
        # Note: we should better remove this (and the same in _reset_matplotlib)
        # and auto-adjust the corresponding config option defaults (image_scrapers, reset_modules) when
        # matplotlib is not present
        return ""

    gallery_conf = script.gallery_conf
    from matplotlib.animation import Animation

    image_mds = []

    # Check for srcset hidpi images
    srcset = gallery_conf.get('image_srcset', [])
    srcset_mult_facs = [1]  # one is always supplied...
    for st in srcset:
        if (len(st) > 0) and (st[-1] == 'x'):
            # "2x" = "2.0"
            srcset_mult_facs += [float(st[:-1])]
        elif st == "":
            pass
        else:
            raise ExtensionError(
                f'Invalid value for image_srcset parameter: "{st}". '
                'Must be a list of strings with the multiplicative '
                'factor followed by an "x".  e.g. ["2.0x", "1.5x"]')

    # Check for animations
    anims = list()
    if gallery_conf.get('matplotlib_animations', False):
        for ani in script.run_vars.example_globals.values():
            if isinstance(ani, Animation):
                anims.append(ani)

    # Then standard images
    for fig_num, image_path in zip(plt.get_fignums(), script.run_vars.image_path_iterator):
        image_path = PurePosixPath(image_path)
        if 'format' in kwargs:
            image_path = image_path.with_suffix('.' + kwargs['format'])

        # Set the fig_num figure as the current figure as we can't save a figure that's not the current figure.
        fig = plt.figure(fig_num)

        # Deal with animations
        cont = False
        for anim in anims:
            if anim._fig is fig:
                image_mds.append(_anim_md(anim, str(image_path), gallery_conf))
                cont = True
                break
        if cont:
            continue

        # get fig titles
        fig_titles = _matplotlib_fig_titles(fig)
        to_rgba = matplotlib.colors.colorConverter.to_rgba

        # shallow copy should be fine here, just want to avoid changing
        # "kwargs" for subsequent figures processed by the loop
        these_kwargs = kwargs.copy()
        for attr in ['facecolor', 'edgecolor']:
            fig_attr = getattr(fig, 'get_' + attr)()
            default_attr = matplotlib.rcParams['figure.' + attr]
            if to_rgba(fig_attr) != to_rgba(default_attr) and \
                    attr not in kwargs:
                these_kwargs[attr] = fig_attr

        # save the figures, and populate the srcsetpaths
        try:
            fig.savefig(image_path, **these_kwargs)
            dpi0 = matplotlib.rcParams['savefig.dpi']
            if dpi0 == 'figure':
                dpi0 = fig.dpi
            dpi0 = these_kwargs.get('dpi', dpi0)
            srcsetpaths = {0: image_path}

            # save other srcset paths, keyed by multiplication factor:
            for mult in srcset_mult_facs:
                if not (mult == 1):
                    multst = f'{mult}'.replace('.', '_')
                    name = f"{image_path.stem}_{multst}x{image_path.suffix}"
                    hipath = image_path.parent / PurePosixPath(name)
                    hikwargs = these_kwargs.copy()
                    hikwargs['dpi'] = mult * dpi0
                    fig.savefig(hipath, **hikwargs)
                    srcsetpaths[mult] = hipath
            srcsetpaths = [srcsetpaths]
        except Exception:
            plt.close('all')
            raise

        if 'images' in gallery_conf['compress_images']:
            optipng(str(image_path), gallery_conf['compress_images_args'])
            for hipath in srcsetpaths[0].items():
                optipng(str(hipath), gallery_conf['compress_images_args'])

        image_mds.append((image_path, fig_titles, srcsetpaths))

    plt.close('all')

    # Create the markdown or html output
    # <li>
    # <img src="../_images/mkd_glr_plot_1_exp_001.png"
    #      srcset="../_images/mkd_glr_plot_1_exp_001.png, ../_images/mkd_glr_plot_1_exp_001_2_0x.png 2.0x"
    #      alt="Exponential function" class="sphx-glr-multi-img">
    # </li>
    # <li>
    # <img src="../_images/mkd_glr_plot_1_exp_002.png"
    #      srcset="../_images/mkd_glr_plot_1_exp_002.png, ../_images/mkd_glr_plot_1_exp_002_2_0x.png 2.0x"
    #      alt="Negative exponential function" class="sphx-glr-multi-img">
    # </li>

    md = ''
    if len(image_mds) == 1:
        if isinstance(image_mds[0], str):
            # an animation, see _anim_md
            md = image_mds[0]
        else:
            # an image
            image_path, fig_titles, srcsetpaths = image_mds[0]
            md = figure_md_or_html([image_path], script, fig_titles, srcsetpaths=srcsetpaths)
    elif len(image_mds) > 1:
        # Old
        # Replace the 'single' CSS class by the 'multi' one
        # image_mds = [re.sub(r"mkd-glr-single-img", "mkd-glr-multi-img", image) for image in image_mds]
        # image_mds = [HLIST_IMAGE_MATPLOTLIB % image for image in image_mds]
        # md = HLIST_HEADER % (''.join(image_mds))

        # New: directly use the html
        image_htmls = []
        for image_path, fig_titles, srcsetpaths in image_mds:
            img_html = figure_md_or_html([image_path], script, fig_titles, srcsetpaths=srcsetpaths, raw_html=True)
            image_htmls.append(img_html)
        md = HLIST_HEADER % (''.join(image_htmls))
    return md


def _anim_md(anim, image_path, gallery_conf):
    import matplotlib
    from matplotlib.animation import FFMpegWriter, ImageMagickWriter
    # output the thumbnail as the image, as it will just be copied
    # if it's the file thumbnail
    fig = anim._fig
    image_path = image_path.replace('.png', '.gif')
    fig_size = fig.get_size_inches()
    thumb_size = gallery_conf['thumbnail_size']
    use_dpi = round(
        min(t_s / f_s for t_s, f_s in zip(thumb_size, fig_size)))
    # FFmpeg is buggy for GIFs before Matplotlib 3.3.1
    if LooseVersion(matplotlib.__version__) >= LooseVersion('3.3.1') and \
            FFMpegWriter.isAvailable():
        writer = 'ffmpeg'
    elif ImageMagickWriter.isAvailable():
        writer = 'imagemagick'
    else:
        writer = None
    anim.save(image_path, writer=writer, dpi=use_dpi)
    html = anim._repr_html_()
    if html is None:  # plt.rcParams['animation.html'] == 'none'
        html = anim.to_jshtml()
    html = indent(html, '     ')
    return _ANIMATION_RST.format(html=html)


def mayavi_scraper(block, script: GalleryScript):
    """Scrape Mayavi images.

    Parameters
    ----------
    block : tuple
        A tuple containing the (label, content, line_number) of the block.

    script : GalleryScript
        Script being run

    Returns
    -------
    md : str
        The ReSTructuredText that will be rendered to HTML containing
        the images. This is often produced by :func:`figure_md_or_html`.
    """
    from mayavi import mlab
    image_path_iterator = script.run_vars.image_path_iterator
    image_paths = list()
    e = mlab.get_engine()
    for scene, image_path in zip(e.scenes, image_path_iterator):
        try:
            mlab.savefig(image_path, figure=scene)
        except Exception:
            mlab.close(all=True)
            raise
        # make sure the image is not too large
        rescale_image(image_path, image_path, 850, 999)
        if 'images' in script.gallery_conf['compress_images']:
            optipng(image_path, script.gallery_conf['compress_images_args'])
        image_paths.append(image_path)
    mlab.close(all=True)
    return figure_md_or_html(image_paths, script)


_scraper_dict = dict(
    matplotlib=matplotlib_scraper,
    mayavi=mayavi_scraper,
)


# For now, these are what we support
_KNOWN_IMG_EXTS = ('.png', '.svg', '.jpg', '.gif')


class ImageNotFoundError(FileNotFoundError):
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return f"Image {self.path} can not be found on disk, with any of the known extensions {_KNOWN_IMG_EXTS}"


def _find_image_ext(path: Path, raise_if_not_found: bool = True) -> Path:
    """Find an image, tolerant of different file extensions."""

    for ext in _KNOWN_IMG_EXTS:
        this_path = path.with_suffix(ext)
        if this_path.exists():
            break
    else:
        if raise_if_not_found:
            raise ImageNotFoundError(path)

        # None exists. Default to png.
        ext = '.png'
        this_path = path.with_suffix(ext)

    return this_path, ext


def save_figures(block, script: GalleryScript):
    """Save all open figures of the example code-block.

    Parameters
    ----------
    block : tuple
        A tuple containing the (label, content, line_number) of the block.

    script : GalleryScript
        Script run.

    Returns
    -------
    images_md : str
        md code to embed the images in the document.
    """
    image_path_iterator = script.run_vars.image_path_iterator
    all_md = u''
    prev_count = len(image_path_iterator)
    for scraper in script.gallery_conf['image_scrapers']:
        # Use the scraper to generate the md containing image(s) (may be several)
        md = scraper(block, script)
        if not isinstance(md, str):
            raise ExtensionError(f"md from scraper {scraper!r} was not a string, got type {type(md)}:\n{md!r}")

        # Make sure that all images generated by the scraper exist.
        n_new = len(image_path_iterator) - prev_count
        for ii in range(n_new):
            current_path, ext = _find_image_ext(image_path_iterator.paths[prev_count + ii])
            if not current_path.exists():
                raise ExtensionError(f"Scraper {scraper!r} did not produce expected image:\n{current_path}")

        all_md += md

    return all_md


def figure_md_or_html(
    figure_paths: List[Path],
    script: GalleryScript,
    fig_titles: str = '',
    srcsetpaths: List[Dict[float, Path]] = None,
    raw_html=False
):
    """Generate md or raw html for a list of image filenames.

    Depending on whether we have one or more figures, we use a
    single md call to 'image' or a horizontal list.

    Parameters
    ----------
    figure_paths : List[Path]
        List of strings of the figures' absolute paths.
    sources_dir : Path
        absolute path of Sphinx documentation sources
    fig_titles : str
        Titles of figures, empty string if no titles found. Currently
        only supported for matplotlib figures, default = ''.
    srcsetpaths : list or None
        List of dictionaries containing absolute paths.  If
        empty, then srcset field is populated with the figure path.
        (see ``image_srcset`` configuration option).  Otherwise,
        each dict is of the form
        {0: /images/image.png, 2.0: /images/image_2_0x.png}
        where the key is the multiplication factor and the contents
        the path to the image created above.

    Returns
    -------
    images_md : str
        md code to embed the images in the document

    The md code will have a custom ``image-sg`` directive that allows
    multiple resolution images to be served e.g.:
    ``:srcset: /plot_types/imgs/img_001.png,
      /plot_types/imgs/img_2_0x.png 2.0x``

    """

    if srcsetpaths is None:
        # this should never happen, but figure_md_or_html is public, so
        # this has to be a kwarg...
        srcsetpaths = [{0: fl} for fl in figure_paths]

    # Get all images relative to the website sources root
    sources_dir = script.gallery.all_info.mkdocs_docs_dir
    script_md_dir = script.gallery.generated_dir

    # Get alt text
    alt = ''
    if fig_titles:
        alt = fig_titles
    elif figure_paths:
        file_name = os.path.split(str(figure_paths[0]))[1]
        # remove ext & 'mkd_glr_' from start & n#'s from end
        file_name_noext = os.path.splitext(file_name)[0][9:-4]
        # replace - & _ with \s
        file_name_final = re.sub(r'[-,_]', ' ', file_name_noext)
        alt = file_name_final

    alt = _single_line_sanitize(alt)

    images_md = ""
    if len(figure_paths) == 1:
        figure_path = figure_paths[0]
        hinames = srcsetpaths[0]
        srcset = _get_srcset_st(sources_dir, hinames)
        if raw_html:
            # html version
            figure_path_rel_to_mkdocs_dir = figure_path.relative_to(sources_dir).as_posix().lstrip('/')
            images_md = f'<img alt="{alt}" src="{figure_path_rel_to_mkdocs_dir}" srcset="{srcset}", ' \
                        f'class="sphx-glr-single-img" />'
        else:
            # markdown version
            figure_path_rel_to_script_md_dir = figure_path.relative_to(script_md_dir).as_posix().lstrip('/')
            images_md = f'![{alt}](./{figure_path_rel_to_script_md_dir}){{: .mkd-glr-single-img srcset="{srcset}"}}'

    elif len(figure_paths) > 1:
        images_md = HLIST_HEADER
        for nn, figure_path in enumerate(figure_paths):
            hinames = srcsetpaths[nn]
            srcset = _get_srcset_st(sources_dir, hinames)
            figure_path_rel_to_mkdocs_dir = figure_path.relative_to(sources_dir).as_posix().lstrip('/')
            images_md += (HLIST_SG_TEMPLATE % (figure_path_rel_to_mkdocs_dir, alt, srcset))

    return images_md


def _get_srcset_st(sources_dir, hinames):
    """
    Create the srcset string for including on the md line.
    ie. sources_dir might be /home/sample-proj/source,
    hinames posix paths to
    0: /home/sample-proj/source/plot_types/images/img1.png,
    2.0: /home/sample-proj/source/plot_types/images/img1_2_0x.png,
    The result will be:
    '/plot_types/basic/images/mkd_glr_pie_001.png,
    /plot_types/basic/images/mkd_glr_pie_001_2_0x.png 2.0x'
    """
    srcst = ''
    for k in hinames.keys():
        path = os.path.relpath(hinames[k],
                               sources_dir).replace(os.sep, '/').lstrip('/')
        srcst += '/' + path
        if k == 0:
            srcst += ', '
        else:
            srcst += f' {k:1.1f}x, '
    if srcst[-2:] == ', ':
        srcst = srcst[:-2]
    srcst += ''

    return srcst


def _single_line_sanitize(s):
    """Remove problematic newlines."""
    # For example, when setting a :alt: for an image, it shouldn't have \n
    # This is a function in case we end up finding other things to replace
    return s.replace('\n', ' ')


# The following strings are used when we have several pictures: we use
# an html div tag that our CSS uses to turn the lists into horizontal
# lists.
HLIST_HEADER = """
<ul class="mkd-glr-horizontal">
%s
</ul>
"""

HLIST_IMAGE_MATPLOTLIB = """<li>
%s
</li>"""

HLIST_SG_TEMPLATE = """
    * ![%s](/%s){: .mkd-glr-multi-img srcset="%s"}
"""


###############################################################################
# Module resetting


def _reset_matplotlib(gallery_conf, file: Path):
    """Reset matplotlib."""
    try:
        import matplotlib
    except ImportError:
        # Matplotlib is not present: do not care
        pass
    else:
        # Proceed with resetting it
        _, plt = _import_matplotlib()
        plt.rcdefaults()


def _reset_seaborn(gallery_conf, file: Path):
    """Reset seaborn."""
    # Horrible code to 'unload' seaborn, so that it resets
    # its default when is load
    # Python does not support unloading of modules
    # https://bugs.python.org/issue9072
    for module in list(sys.modules.keys()):
        if 'seaborn' in module:
            del sys.modules[module]


_reset_dict = {
    'matplotlib': _reset_matplotlib,
    'seaborn': _reset_seaborn,
}


def clean_modules(gallery_conf: Dict, file: Optional[Path]):
    """Remove, unload, or reset modules after running each example.

    After a script is executed it can load a variety of settings that one
    does not want to influence in other examples in the gallery.

    Parameters
    ----------
    gallery_conf : dict
        The gallery configuration.

    file : Path
        The example being run. Will be None when this is called entering
        a directory of examples to be built.
    """
    for reset_module in gallery_conf['reset_modules']:
        reset_module(gallery_conf, file)
