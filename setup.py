from setuptools import setup, find_packages

version = '0.0.4'

setup(
    name='django-proctor',
    version=version,
    packages=find_packages(),
    install_requires=['Django', 'requests', 'pyOpenSSL', 'ndg-httpsclient'],
)
