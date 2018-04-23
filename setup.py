from setuptools import setup, find_packages

version = '0.0.7'

setup(
    name='django-proctor',
    version=version,
    install_requires=['Django', 'requests', 'pyOpenSSL', 'ndg-httpsclient'],
)
