from setuptools import setup, find_packages

setup(
    name = "cyberpyg",
    version = "0.09",
    packages=find_packages(),
    dependency_links = [],
    install_requires=['colorama', 'pygments'],
    extras_require={},
    package_data = {},
    author="David Barnett",
    author_email = "davidbarnett2@gmail.com",
    description = "syntax highlighting / lexing framework",
    license = "BSD",
    keywords= "",
    url = "http://github.com/dbarnett/cyberpyg",
    entry_points = {
        "console_scripts": [
        ]
    }
)
