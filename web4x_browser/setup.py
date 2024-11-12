from setuptools import setup, find_packages

setup(
    name="web4x_browser",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "PyQt6",  # Specify other dependencies if needed
        "PyQt6-WebEngine",
    ],
    entry_points={
        "console_scripts": [
            "web4x-browser=web4x_browser.main:main",  # Command to run the app
        ]
    },
    author="Hannes Nortjé",
    description="A Web 4.0 platform browser using PyQt6",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    license="AGPL-3.0-or-later",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
