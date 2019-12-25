#!/usr/bin/env python


"""
@PROJECT: proxy_twisted
@AUTHOR: momen
@TIME: 12/25/19 9:27 AM
"""


from setuptools import setup, find_packages

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='proxy_twisted',
    version='0.3.0',
    description='proxy pool based in twisted',
    long_description=long_description,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=True
)