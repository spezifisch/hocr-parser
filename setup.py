#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

REQUIRED_PACKAGES = [
    'beautifulsoup4',
]

TESTING_PACKAGES = [
    'tox',
    'pytest',
    'pytest-cov',
    'pytest-random-order',
    'flake8'
]

setup(
    name='hocr-parser',
    version='0.4',
    description='HOCR Specification Python Parser',
    author='Athento',
    author_email='rh@athento.com',
    url='https://github.com/athento/hocr-parser',
    license='Apache 2.0 License',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: OCR'
    ],
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*"]),
    install_requires=REQUIRED_PACKAGES,
    tests_require=REQUIRED_PACKAGES + TESTING_PACKAGES,
    extras_require={
        'testing': REQUIRED_PACKAGES + TESTING_PACKAGES,
    },
)
