#!/usr/bin/env python3
"""
Setup script for PKI Monitor Python application.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

setup(
    name="pki-monitor-py",
    version="1.0.0",
    author="PKI Monitor Team",
    description="PKI Site Health Check - Monitor ZETES / eID PKI services",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/pki-monitor-py",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Security",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.7",
    install_requires=[
        # No external dependencies - uses only Python standard library
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "enhanced": [
            "requests>=2.31.0",
            "python-ldap>=3.4.0",
            "pandas>=2.0.0",
            "loguru>=0.7.0",
            "pyyaml>=6.0",
            "tqdm>=4.65.0",
        ],
        "ui": [
            "streamlit>=1.36.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pki-monitor=pki_monitor:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
