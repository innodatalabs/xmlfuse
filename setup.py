from setuptools import setup
from xmlfuse import __version__, __description__, __url__, __author__, \
    __author_email__, __keywords__

NAME = 'xmlfuse'

with open('README.md') as f:
    long_description = f.read()

setup(
    name=NAME,
    version=__version__,
    description=__description__,
    url=__url__,
    author=__author__,
    author_email=__author_email__,
    keywords=__keywords__,

    long_description=long_description,
    long_description_content_type='text/markdown',

    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    packages=[NAME],
    install_requires=['lxml', 'lxmlx']
)
