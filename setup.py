import setuptools
import importlib

module = importlib.import_module(setuptools.find_packages()[0])

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name=module.__name__,
    version=".".join(str(n) for n in module.__version__),
    author=module.__author__["name"],
    author_email=module.__author__["email"],
    description=module.__desc__,
	license="GPLv3",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/" + module.__author__["github"] + "/" + module.__name__,
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
	python_requires=">=3.5",
	install_requires=module.__requires__,
	package_data={'': module.__resources__},
	include_package_data=True,
	entry_points = {
		"console_scripts":[
			cmd + " = " + module.__name__ + "." + module.__commands__[cmd]
			for cmd in module.__commands__
		]
	}
)
