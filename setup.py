import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

__tag__ = ""
__build__ = 0
__version__ = "{}".format(__tag__)

setuptools.setup(
    name="binalyzer_rest",
    version=__version__,
    author="Denis Vasilìk",
    author_email="contact@denisvasilik.com",
    url="https://binalyzer.denisvasilik.com",
    project_urls={
        "Bug Tracker": "https://github.com/denisvasilik/binalyzer/issues/",
        "Documentation": "https://binalyzer.readthedocs.io/en/latest/",
        "Source Code": "https://github.com/denisvasilik/binalyzer/",
    },
    description="Binary Data Analyzer",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Operating System :: POSIX :: Linux",
    ],
    dependency_links=[],
    package_dir={"binalyzer_rest": "binalyzer_rest"},
    package_data={
        'binalyzer_rest' : ['resources/*.yml']
    },
    data_files=[("", ["CHANGELOG.md"])],
    setup_requires=[],
    install_requires=[
        "binalyzer",
        "click>=5.1",
        "flask>=1.0",
        "flasgger>=0.9.3",
        "jsonschema>=2.6.0",
        "requests>=2.25.1"
    ],
    entry_points='''
        [binalyzer.commands]
        rest=binalyzer_rest.cli:rest
    ''',
)
