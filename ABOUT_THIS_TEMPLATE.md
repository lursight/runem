# About this template

Hi, I created this template to help you get started with a new project.

I have created and maintained a number of python libraries, applications and 
frameworks and during those years I have learned a lot about how to create a 
project structure and how to structure a project to be as modular and simple 
as possible.

Some decisions I have made while creating this template are:

 - Create a project structure that is as modular as possible.
 - Keep it simple and easy to maintain.
 - Allow for a lot of flexibility and customizability.
 - Low dependency (this template doesn't add dependencies)

## Structure

Lets take a look at the structure of this template:

```text
├── Containerfile            # The file to build a container using buildah or docker
├── CONTRIBUTING.md          # Onboarding instructions for new contributors
├── docs                     # Documentation site (add more .md files here)
│   └── index.md             # The index page for the docs site
├── .github                  # Github metadata for repository
│   ├── release_message.sh   # A script to generate a release message
│   └── workflows            # The CI pipeline for Github Actions
├── .gitignore               # A list of files to ignore when pushing to Github
├── HISTORY.md               # Auto generated list of changes to the project
├── LICENSE                  # The license for the project
├── Makefile                 # A collection of utilities to manage the project
├── MANIFEST.in              # A list of files to include in a package
├── mkdocs.yml               # Configuration for documentation site
├── runem                    # The main python package for the project
│   ├── base.py              # The base module for the project
│   ├── __init__.py          # This tells Python that this is a package
│   ├── __main__.py          # The entry point for the project
│   └── VERSION              # The version for the project is kept in a static file
├── README.md                # The main readme for the project
├── setup.py                 # The setup.py file for installing and packaging the project
├── requirements.txt         # An empty file to hold the requirements for the project
├── requirements-test.txt    # List of requirements for testing and development
├── setup.py                 # The setup.py file for installing and packaging the project
└── tests                    # Unit tests for the project (add mote tests files here)
    ├── conftest.py          # Configuration, hooks and fixtures for pytest
    ├── __init__.py          # This tells Python that this is a test package
    └── test_base.py         # The base test case for the project
```

## FAQ

Frequent asked questions.

### Why this template is not using [Poetry](https://python-poetry.org/) ?

I really like Poetry and I think it is a great tool to manage your python projects,
if you want to switch to poetry, you can run `make switch-to-poetry`.

But for this template I wanted to keep it simple.

Setuptools is the most simple and well supported way of packaging a Python project,
it doesn't require extra dependencies and is the easiest way to install the project.

Also, poetry doesn't have a good support for installing projects in development mode yet.

### Why the `requirements.txt` is empty ?

This template is a low dependency project, so it doesn't have any extra dependencies.

### Why there is a `requirements-test.txt` file ?

This file lists all the requirements for testing and development,
I think the development environment and testing environment should be as similar as possible.

### Why `VERSION` is kept in a static plain text file?

I used to have my version inside my main module in a `__version__` variable, then
I had to do some tricks to read that version variable inside the setuptools 
`setup.py` file because that would be available only after the installation.

I decided to keep the version in a static file because it is easier to read from
wherever I want without the need to install the package.

e.g: `cat runem/VERSION` will get the project version without harming
with module imports or anything else, it is useful for CI, logs and debugging.

### Why to include `tests`, `history` and `Containerfile` as part of the release?

The `MANIFEST.in` file is used to include the files in the release, once the 
project is released to PyPI all the files listed on MANIFEST.in will be included
even if the files are static or not related to Python.

Some build systems such as RPM, DEB, AUR for some Linux distributions, and also
internal repackaging systems tends to run the tests before the packaging is performed.

The Containerfile can be useful to provide a safer execution environment for 
the project when running on a testing environment.

I added those files to make it easier for packaging in different formats.

### Why conftest includes a go_to_tmp_path_ fixture?

When your project deals with file system operations, it is a good idea to use
a fixture to create a temporary directory and then remove it after the test.

Before executing each test pytest will create a temporary directory and will
change the working directory to that path and run the test.

So the test can create temporary artifacts isolated from other tests.

After the execution Pytest will remove the temporary directory.

### Why this template is not using [pre-commit](https://pre-commit.com/) ?

pre-commit is an excellent tool to automate checks and formatting on your code.

However I figured out that pre-commit adds extra dependency and it an entry barrier
for new contributors.

Having the linting, checks and formatting as simple commands on the [Makefile](Makefile)
makes it easier to understand and change.

Once the project is bigger and complex, having pre-commit as a dependency can be a good idea.

### Why the CLI is not using click?

I wanted to provide a simple template for a CLI application on the project main entry point
click and other tools are great alternatives but are external dependencies and this template
doesn't add dependencies besides those used for development.

## The Makefile

All the utilities for the template and project are on the Makefile

```bash
❯ make
Usage: make <target>

Targets:
help:             ## Show the help.
install:          ## Install the project in dev mode.
fmt:              ## Format code using black & isort.
lint:             ## Run pep8, black, mypy linters.
test: lint        ## Run tests and generate coverage report.
watch:            ## Run tests on every change.
clean:            ## Clean unused files.
virtualenv:       ## Create a virtual environment.
release:          ## Create a new tag for release.
docs:             ## Build the documentation.
switch-to-poetry: ## Switch to poetry package manager.
init:             ## Initialize the project based on an application template.
```
