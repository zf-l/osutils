# encoding=utf-8
from setuptools import setup, find_packages
import codecs
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with codecs.open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='osutils',
    version='0.1.0',
    description='Windows Automaiton test utils lib',
    long_description=long_description,
    url='https://github.com/zf-l/osutils',
    author='zf-l',
    author_email='zf.liu@foxmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development ::  Application Frameworks',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        #'Programming Language :: Python :: 3.5',
    ],

    keywords='Windows autotest library',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=['pywin32', 'chardet', 'wmi'],

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    extras_require={
        'dev': ['check-manifest'],
        'test': ['coverage'],
    },
)