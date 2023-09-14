from setuptools import setup, find_packages
import sys

install_requires = [
    "PyQt6==6.4.1",
    "PyQt6-QScintilla==2.14.1",
    "psutil==5.9.4",
    "filetype",
]
if sys.platform == "win32":
    install_requires.append("pywin32==305")

setup(
    name="cipher",
    version="1.1.1",
    description="A text editor made using PyQt6",
    author="Srpboyz",
    url="https://github.com/Srpboyz/Cipher",
    packages=find_packages(where="cipher"),
    package_dir={"": "cipher"},
    python_requires=">=3.9",
    install_requires=install_requires,
    entry_points={
        "console_scripts": [
            "cipher = cipher.__main__:run",
            "Cipher = cipher.__main__:run",
        ]
    },
)
