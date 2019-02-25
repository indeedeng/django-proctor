from setuptools import setup, find_packages

version = '1.0.1'

setup(
    name='django-proctor',
    version=version,
    install_requires=['Django', 'requests', 'pyOpenSSL', 'ndg-httpsclient'],
)
