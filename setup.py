from __future__ import absolute_import, unicode_literals

from setuptools import setup, find_packages
from os import path


here = path.abspath(path.dirname(__file__))
# Get the long description from the README file
with open(path.join(here, 'README.md')) as f:
    long_description = f.read()

setup(
    name='django-proctor',
    version='1.1.0',
    description="Django library for interacting with the Proctor A/B testing framework",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/indeedeng/django-proctor',
    packages=find_packages(),
    include_package_data=True,
    license='Apache',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.11',
        'Framework :: Django :: 2.0',
        'Framework :: Django :: 2.1',
        'Framework :: Django :: 2.2',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
    install_requires=[
        'Django',
        'ndg-httpsclient',
        'pyOpenSSL',
        'requests',
        'tenacity>=4.8.0',
    ],
    zip_safe=False,
)
