import argparse
from itertools import product
from json import dumps
import logging

import nox  # noqa
from pathlib import Path  # noqa
import sys

# add parent folder to python path so that we can import noxfile_utils.py
# note that you need to "pip install -r noxfile-requiterements.txt" for this file to work.
sys.path.append(str(Path(__file__).parent / "ci_tools"))
from nox_utils import PY27, PY37, PY36, PY35, PY38, PY39, PY310, PY311, power_session, rm_folder, rm_file, PowerSession  # noqa


pkg_name = "mkdocs_gallery"
gh_org = "smarie"
gh_repo = "mkdocs-gallery"

ENVS = {
    PY311: {"coverage": False, "pkg_specs": {"pip": ">19"}},
    PY310: {"coverage": False, "pkg_specs": {"pip": ">19"}},
    PY39: {"coverage": False, "pkg_specs": {"pip": ">19"}},
    PY37: {"coverage": False, "pkg_specs": {"pip": ">19"}},
    # IMPORTANT: this should be last so that the folder docs/reports is not deleted afterwards
    PY38: {"coverage": True, "pkg_specs": {"pip": ">19"}},
}


# set the default activated sessions, minimal for CI
nox.options.sessions = ["tests", "flake8", "docs"]  # , "docs", "gh_pages"
nox.options.error_on_missing_interpreters = True
nox.options.reuse_existing_virtualenvs = True  # this can be done using -r
# if platform.system() == "Windows":  >> always use this for better control
nox.options.default_venv_backend = "virtualenv"
# os.environ["NO_COLOR"] = "True"  # nox.options.nocolor = True does not work
# nox.options.verbose = True

nox_logger = logging.getLogger("nox")
# nox_logger.setLevel(logging.INFO)  NO !!!! this prevents the "verbose" nox flag to work !


class Folders:
    root = Path(__file__).parent
    ci_tools = root / "ci_tools"
    runlogs = root / Path(nox.options.envdir or ".nox") / "_runlogs"
    runlogs.mkdir(parents=True, exist_ok=True)
    dist = root / "dist"
    site = root / "site"
    site_reports = site / "reports"
    reports_root = root / "docs" / "reports"
    test_reports = reports_root / "junit"
    test_xml = test_reports / "junit.xml"
    test_html = test_reports / "report.html"
    test_badge = test_reports / "junit-badge.svg"
    coverage_reports = reports_root / "coverage"
    coverage_xml = coverage_reports / "coverage.xml"
    coverage_intermediate_file = root / ".coverage"
    coverage_badge = coverage_reports / "coverage-badge.svg"
    flake8_reports = reports_root / "flake8"
    flake8_intermediate_file = root / "flake8stats.txt"
    flake8_badge = flake8_reports / "flake8-badge.svg"


@power_session(envs=ENVS, logsdir=Folders.runlogs)
def tests(session: PowerSession, coverage, pkg_specs):
    """Run the test suite, including test reports generation and coverage reports. """

    # As soon as this runs, we delete the target site and coverage files to avoid reporting wrong coverage/etc.
    rm_folder(Folders.site)
    rm_folder(Folders.reports_root)
    # delete the .coverage files if any (they are not supposed to be any, but just in case)
    rm_file(Folders.coverage_intermediate_file)
    rm_file(Folders.root / "coverage.xml")

    # CI-only dependencies
    # Did we receive a flag through positional arguments ? (nox -s tests -- <flag>)
    # install_ci_deps = False
    # if len(session.posargs) == 1:
    #     assert session.posargs[0] == "keyrings.alt"
    #     install_ci_deps = True
    # elif len(session.posargs) > 1:
    #     raise ValueError("Only a single positional argument is accepted, received: %r" % session.posargs)

    # uncomment and edit if you wish to uninstall something without deleting the whole env
    # session.run2("pip uninstall pytest-asyncio --yes")

    # install all requirements
    session.install_reqs(setup=True, install=True, tests=True, versions_dct=pkg_specs)

    # Since our tests are currently limited, use our own doc generation as a test
    session.install_reqs(phase="tests", phase_reqs=MKDOCS_GALLERY_EXAMPLES_REQS)

    # install CI-only dependencies
    # if install_ci_deps:
    #     session.install2("keyrings.alt")

    # list all (conda list alone does not work correctly on github actions)
    # session.run2("conda list")
    # conda_prefix = Path(session.bin)
    # if conda_prefix.name == "bin":
    #     conda_prefix = conda_prefix.parent
    # session.run2("conda list", env={"CONDA_PREFIX": str(conda_prefix), "CONDA_DEFAULT_ENV": session.get_session_id()})

    # Fail if the assumed python version is not the actual one
    session.run2("python ci_tools/check_python_version.py %s" % session.python)

    # finally run all tests
    if not coverage:
        # install self so that it is recognized by pytest
        session.install2('.', '--no-deps')

        # simple: pytest only
        session.run2("python -m pytest --cache-clear -v tests/")

        # since our tests are too limited, we use our own mkdocs build as additional test for now.
        session.run2("python -m mkdocs build")
        # -- add a second build so that we can go through the caching/md5 side
        session.run2("python -m mkdocs build")
    else:
        # install self in "develop" mode so that coverage can be measured
        session.install2('-e', '.', '--no-deps')

        # coverage + junit html reports + badge generation
        session.install_reqs(phase="coverage",
                             phase_reqs=["coverage", "pytest-html", "genbadge[tests,coverage]"],
                             versions_dct=pkg_specs)

        # --coverage + junit html reports
        session.run2("coverage run --source src/{pkg_name} "
                     "-m pytest --cache-clear --junitxml='{test_xml}' --html='{test_html}' -v tests/"
                     "".format(pkg_name=pkg_name, test_xml=Folders.test_xml, test_html=Folders.test_html))

        # -- use the doc generation for coverage
        session.run2("coverage run --append --source src/{pkg_name} -m mkdocs build"
                     "".format(pkg_name=pkg_name, test_xml=Folders.test_xml, test_html=Folders.test_html))
        # -- add a second build so that we can go through the caching/md5 side
        session.run2("coverage run --append --source src/{pkg_name} -m mkdocs build"
                     "".format(pkg_name=pkg_name, test_xml=Folders.test_xml, test_html=Folders.test_html))

        session.run2("coverage report")
        session.run2("coverage xml -o '{covxml}'".format(covxml=Folders.coverage_xml))
        session.run2("coverage html -d '{dst}'".format(dst=Folders.coverage_reports))
        # delete this intermediate file, it is not needed anymore
        rm_file(Folders.coverage_intermediate_file)

        # --generates the badge for the test results and fail build if less than x% tests pass
        nox_logger.info("Generating badge for tests coverage")
        # Use our own package to generate the badge
        session.run2("genbadge tests -i '%s' -o '%s' -t 100" % (Folders.test_xml, Folders.test_badge))
        session.run2("genbadge coverage -i '%s' -o '%s'" % (Folders.coverage_xml, Folders.coverage_badge))


@power_session(python=PY39, logsdir=Folders.runlogs)
def flake8(session: PowerSession):
    """Launch flake8 qualimetry."""

    session.install("-r", str(Folders.ci_tools / "flake8-requirements.txt"))
    session.install("genbadge[flake8]")
    session.install2('.')

    rm_folder(Folders.flake8_reports)
    Folders.flake8_reports.mkdir(parents=True, exist_ok=True)
    rm_file(Folders.flake8_intermediate_file)

    session.cd("src")

    # Options are set in `setup.cfg` file
    session.run("flake8", pkg_name, "--exit-zero", "--format=html", "--htmldir", str(Folders.flake8_reports),
                "--statistics", "--tee", "--output-file", str(Folders.flake8_intermediate_file))
    # generate our badge
    session.run2("genbadge flake8 -i '%s' -o '%s'" % (Folders.flake8_intermediate_file, Folders.flake8_badge))
    rm_file(Folders.flake8_intermediate_file)


MKDOCS_GALLERY_EXAMPLES_REQS = [
    "matplotlib",
    "seaborn",
    "statsmodels",
    "plotly",
    "pyvista",
    # "memory_profiler",
    "pillow"  # PIL, required for image rescaling
]


@power_session(python=[PY39])
def docs(session: PowerSession):
    """Generates the doc and serves it on a local http server. Pass '-- build' to build statically instead."""

    session.install_reqs(phase="docs", phase_reqs=["mkdocs"] + MKDOCS_GALLERY_EXAMPLES_REQS)

    # Install the plugin
    session.install2('.')

    if session.posargs:
        # use posargs instead of "serve"
        session.run2("mkdocs %s" % " ".join(session.posargs))
    else:
        session.run2("mkdocs serve")


@power_session(python=[PY39])
def publish(session: PowerSession):
    """Deploy the docs+reports on github pages. Note: this rebuilds the docs"""

    session.install_reqs(
        phase="mkdocs",
        phase_reqs=["mkdocs"] + MKDOCS_GALLERY_EXAMPLES_REQS
    )

    # Install the plugin
    session.install2('.')

    # possibly rebuild the docs in a static way (mkdocs serve does not build locally)
    session.run2("mkdocs build")

    # check that the doc has been generated with coverage
    if not Folders.site_reports.exists():
        raise ValueError("Test reports have not been built yet. Please run 'nox -s tests-3.7' first")

    # publish the docs
    session.run2("mkdocs gh-deploy")

    # publish the coverage - now in github actions only
    # session.install_reqs(phase="codecov", phase_reqs=["codecov", "keyring"])
    # # keyring set https://app.codecov.io/gh/<org>/<repo> token
    # import keyring  # (note that this import is not from the session env but the main nox env)
    # codecov_token = keyring.get_password("https://app.codecov.io/gh/<org>/<repo>>", "token")
    # # note: do not use --root nor -f ! otherwise "There was an error processing coverage reports"
    # session.run2('codecov -t %s -f %s' % (codecov_token, Folders.coverage_xml))


@power_session(python=[PY39])
def release(session: PowerSession):
    """Create a release on github corresponding to the latest tag"""

    # Get current tag using setuptools_scm and make sure this is not a dirty/dev one
    from setuptools_scm import get_version  # (note that this import is not from the session env but the main nox env)
    from setuptools_scm.version import guess_next_dev_version
    version = []

    def my_scheme(version_):
        version.append(version_)
        return guess_next_dev_version(version_)
    current_tag = get_version(".", version_scheme=my_scheme)

    # create the package
    session.install_reqs(phase="setup.py#dist", phase_reqs=["setuptools_scm"])
    rm_folder(Folders.dist)
    session.run2("python setup.py sdist bdist_wheel")

    if version[0].dirty or not version[0].exact:
        raise ValueError("You need to execute this action on a clean tag version with no local changes.")

    # Did we receive a token through positional arguments ? (nox -s release -- <token>)
    if len(session.posargs) == 1:
        # Run from within github actions - no need to publish on pypi
        gh_token = session.posargs[0]
        publish_on_pypi = False

    elif len(session.posargs) == 0:
        # Run from local commandline - assume we want to manually publish on PyPi
        publish_on_pypi = True

        # keyring set https://docs.github.com/en/rest token
        import keyring  # (note that this import is not from the session env but the main nox env)
        gh_token = keyring.get_password("https://docs.github.com/en/rest", "token")
        assert len(gh_token) > 0

    else:
        raise ValueError("Only a single positional arg is allowed for now")

    # publish the package on PyPi
    if publish_on_pypi:
        # keyring set https://upload.pypi.org/legacy/ your-username
        # keyring set https://test.pypi.org/legacy/ your-username
        session.install_reqs(phase="PyPi", phase_reqs=["twine"])
        session.run2("twine upload dist/* -u smarie")  # -r testpypi

    # create the github release
    session.install_reqs(phase="release", phase_reqs=["click", "PyGithub"])
    session.run2("python ci_tools/github_release.py -s {gh_token} "
                 "--repo-slug {gh_org}/{gh_repo} -cf ./docs/changelog.md "
                 "-d https://{gh_org}.github.io/{gh_repo}/changelog {tag}"
                 "".format(gh_token=gh_token, gh_org=gh_org, gh_repo=gh_repo, tag=current_tag))


@nox.session(python=False)
def gha_list(session):
    """(mandatory arg: <base_session_name>) Prints all sessions available for <base_session_name>, for GithubActions."""

    # see https://stackoverflow.com/q/66747359/7262247

    # The options
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--session", help="The nox base session name")
    parser.add_argument(
        "-v",
        "--with_version",
        action="store_true",
        default=False,
        help="Return a list of lists where the first element is the python version and the second the nox session.",
    )
    additional_args = parser.parse_args(session.posargs)

    # get the desired base session to generate the list for
    session_func = globals()[additional_args.session]

    # list all sessions for this base session
    try:
        session_func.parametrize
    except AttributeError:
        if additional_args.with_version:
            sessions_list = [{"python": py, "session": "%s-%s" % (session_func.__name__, py)} for py in session_func.python]
        else:
            sessions_list = ["%s-%s" % (session_func.__name__, py) for py in session_func.python]
    else:
        if additional_args.with_version:
            sessions_list = [{"python": py, "session": "%s-%s(%s)" % (session_func.__name__, py, param)}
                             for py, param in product(session_func.python, session_func.parametrize)]
        else:
            sessions_list = ["%s-%s(%s)" % (session_func.__name__, py, param)
                             for py, param in product(session_func.python, session_func.parametrize)]

    # print the list so that it can be caught by GHA.
    # Note that json.dumps is optional since this is a list of string.
    # However it is to remind us that GHA expects a well-formatted json list of strings.
    print(dumps(sessions_list))


# if __name__ == '__main__':
#     # allow this file to be executable for easy debugging in any IDE
#     nox.run(globals())
