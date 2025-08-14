#!/usr/bin/env python3
"""
Setup script for Remote ID Python Library
"""

from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read requirements
with open(os.path.join(this_directory, 'requirements.txt'), encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="remote-id-python",
    version="1.0.0",
    author="Jan Mikołajczyk",
    author_email="jan.mikolajczyk@example.com",
    description="Comprehensive Python library for Remote ID drone data decoding and monitoring",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/janmikolajczyk/remote-id-python",
    
    # Package configuration
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    
    # Dependencies
    install_requires=requirements,
    
    # Optional dependencies
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'black>=22.0.0',
            'isort>=5.0.0',
            'flake8>=4.0.0',
        ],
        'docs': [
            'sphinx>=4.0.0',
            'sphinx-rtd-theme>=1.0.0',
        ],
    },
    
    # Entry points for CLI commands
    entry_points={
        'console_scripts': [
            'remote-id-decode=remote_id.cli:decode_command',
            'remote-id-monitor=remote_id.cli:monitor_command',
            'remote-id-live=remote_id.cli:live_command',
        ],
    },
    
    # Classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research", 
        "Topic :: Scientific/Engineering",
        "Topic :: System :: Hardware",
        "Topic :: Communications",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    
    # Python version requirement
    python_requires=">=3.8",
    
    # Include additional files
    include_package_data=True,
    package_data={
        'remote_id': ['data/*.json', 'templates/*.txt'],
    },
    
    # Project URLs
    project_urls={
        "Bug Reports": "https://github.com/janmikolajczyk/remote-id-python/issues",
        "Source": "https://github.com/janmikolajczyk/remote-id-python",
        "Documentation": "https://remote-id-python.readthedocs.io/",
    },
    
    # Keywords for PyPI search
    keywords="drone remote-id astm-f3411 ble wifi-nan aviation uav",
    
    # License
    license="MIT",
)