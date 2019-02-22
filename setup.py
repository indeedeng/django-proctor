from __future__ import absolute_import, unicode_literals

from setuptools import setup, find_packages

version = '0.0.8'

setup(
    name='django-proctor',
    version=version,
    install_requires=[
        'Django<2.0',
        'ndg-httpsclient',
        'pyOpenSSL',
        'requests',
    ],
)
