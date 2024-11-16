"""Python setup.py for runem package."""

import io
import os
import typing

from setuptools import find_packages, setup


def read(*paths: str, **kwargs: typing.Any) -> str:
    """Read the contents of a text file safely.

    >>> read("runem", "VERSION")
    '0.0.0'
    >>> read("README.md")
    ...
    """

    content = ""
    with io.open(
        os.path.join(os.path.dirname(__file__), *paths),
        encoding=kwargs.get("encoding", "utf8"),
    ) as open_file:
        content = open_file.read().strip()
    return content


def read_requirements(path: str) -> typing.List[str]:
    return [
        line.strip()
        for line in read(path).split("\n")
        if not line.startswith(('"', "#", "-", "git+"))
    ]


setup(
    name="runem",
    version=read("runem", "VERSION"),
    description="Awesome runem created by lursight",
    url="https://github.com/lursight/runem/",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    author="lursight",
    packages=find_packages(exclude=["tests", ".github"]),
    package_data={
        "runem": ["VERSION"],  # Specify the path to VERSION within the package
    },
    install_requires=read_requirements("requirements.txt"),
    entry_points={"console_scripts": ["runem = runem.__main__:main"]},
    extras_require={"tests": read_requirements("requirements-test.txt")},
)
