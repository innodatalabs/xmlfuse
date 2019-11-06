# lxmlx
[![Build Status](https://travis-ci.org/innodatalabs/xmlfuse.svg?branch=master)](https://travis-ci.org/innodatalabs/xmlfuse)
[![PyPI version](https://badge.fury.io/py/xmlfuse.svg)](https://badge.fury.io/py/xmlfuse)

Given two XML documents having the same text, fuses the markup together to create the output XML document.

## Installation

If you install using `pip`, all dependencies are automatically fetched and installed:

```
pip install xmlfuse
```

If you want to build from sources, follow these steps:

### Building and testing:
```
make venv
make
```

## API
```python
import lxml.etree as et
from xmlfuse.fuse import fuse

xml1 = et.fromstring('<span>Hello, <i>world!</i></span>')
xml2 = et.fromstring('<span><b>Hello</b>, world!</span>')

xml = fuze(xml1, xml2)
assert et.tostring(xml) == b'<span><b>Hello</b>, <i>world!</i></span>'
```
