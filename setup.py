from __future__ import absolute_import, unicode_literals

from setuptools import setup, find_packages

version = '1.0.1'

setup(
    name='django-proctor',
    version=version,
    install_requires=['Django', 'ndg-httpsclient', 'pyOpenSSL', 'requests'],
)
