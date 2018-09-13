#!/usr/bin/env python
from setuptools import setup, find_packages
try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except(IOError, ImportError):
    long_description = open('README.md').read()

setup(
    name='ziprecruiter',
    version='1.0.1',
    description='An unofficial ziprecruiter api for applying to jobs,login,search, uploading new resumes, and more!',
    long_description=long_description,
    packages=find_packages(),
    url='https://github.com/ConnorSMaynes/ziprecruiter',
    license='MIT License',
    author='ConnorSMaynes',
    author_email='connormaynes@gmail.com',
    maintainer='ConnorSMaynes',
    maintainer_email='connormaynes@gmail.com',
    platforms=["all"],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        "Programming Language :: Python :: 3",
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries'
    ]
)