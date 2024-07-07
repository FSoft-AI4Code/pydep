import setuptools

with open("README.md", "r", encoding = "utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name = "pydepcall",
    version = "0.0.1",
    author = "Nam Le Hai",
    author_email = "nam.lh173264@gmail.com",
    description = "Extract dependencies of modules (function, class, import) in python repository",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = "https://github.com/FSoft-AI4Code/pydepcall",
    project_urls = {
        "repository": "https://github.com/FSoft-AI4Code/pydepcall",
    },
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir = {"": "src"},
    packages = setuptools.find_packages(where="src"),
    python_requires = ">=3.10"
)
