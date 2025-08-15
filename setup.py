#!/usr/bin/env python3
"""
Setup script for Git Repository Viewer

This allows the package to be installed as:
    pip install -e .
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
if requirements_path.exists():
    with open(requirements_path, 'r') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
else:
    requirements = [
        'wxPython>=4.2.0',
        'GitPython>=3.1.40', 
        'Pillow>=10.0.0',
        'python-dateutil>=2.8.2'
    ]

setup(
    name="git-repository-viewer",
    version="1.0.0",
    author="Git Viewer Team",
    author_email="",
    description="A comprehensive Git and Meta repository management tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/git-repository-viewer",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Version Control :: Git",
        "Topic :: Software Development :: User Interfaces",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
    },
    entry_points={
        "console_scripts": [
            "git-viewer=git_viewer.__main__:main",
            "git-repository-viewer=git_viewer.__main__:main",
        ],
        "gui_scripts": [
            "git-viewer-gui=git_viewer.__main__:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="git repository viewer gui wxpython version-control",
    project_urls={
        "Bug Reports": "https://github.com/your-username/git-repository-viewer/issues",
        "Source": "https://github.com/your-username/git-repository-viewer",
        "Documentation": "https://github.com/your-username/git-repository-viewer/blob/main/README.md",
    },
)
