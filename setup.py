#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [ "django>3"]

test_requirements = ['pytest>=3', ]

setup(
    author="Arun Tigeraniya",
    author_email='tigeraniya@gmail.com',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Populate initial data for development purposes & testing easily.",
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='populate_data_deterministic',
    name='populate_data_deterministic',
    packages=find_packages(include=['populate_data_deterministic', 'populate_data_deterministic.*']),
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/tigeraniya/populate_data_deterministic',
    version='0.2.3',
    zip_safe=False,
)
