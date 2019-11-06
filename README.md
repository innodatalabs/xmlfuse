# xmlfuse
[![Build Status](https://travis-ci.org/innodatalabs/xmlfuse.svg?branch=master)](https://travis-ci.org/innodatalabs/xmlfuse)
[![PyPI version](https://badge.fury.io/py/xmlfuse.svg)](https://badge.fury.io/py/xmlfuse)

Given two XML documents having the same text, fuses the markup together to create the output XML document.

## Installation

```
pip install xmlfuse
```

### Building and testing:
If you prefer to build from sources, follow these steps:

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

# Input documents must have exactly the same text
Error is raised if text differs. Whitespace does matter!

Example:
```python
xml1 = et.fromstring('<span>Hello</span>')
xml2 = et.fromstring('<span>Good bye</span>')

xml = fuze(xml1, xml2)
# expect RuntimeError raised
```

# Conflicting markup
Sometimes it is not possible to merge two markups, because tags intersect. In such a case one has a choice:

  a. Raise an exception and let caller handle the problem
  b. Resolve by segmenting one of the markups

We treat first document as **master**, and second as **slave**. Master markup is never segmented. If there is a
conflict between master and slave markups (and if `auto_segment` flag is `True`), `fuse()` will segment slave to make markup consistent.

Example:
```python
xml1 = et.fromstring('<span>Hel<i>lo, world!</i></span>')
xml2 = et.fromstring('<span><b>Hello</b>, world!</span>')

xml = fuze(xml1, xml2)
assert et.tostring(xml) == b'<span><b>Hel<i>lo</i></b></i>, <i>world!</i></span>'
```

Set `auto_segment` flag to `False` to prevent segmentation. Error will be raised instead, if conflict detected.

# Ambiguities
When master ans slave markups wrap the same text, there is a nesting ambuguity - which tag should be inner?

We resolve this by consistently trying to put **slave** markup inside the **master**. This behavior can be changed
by setting the flag `prefer_slave_inner` to false.

Example:
```python
xml1 = et.fromstring('<span><i>Hello</i>, world!</span>')
xml2 = et.fromstring('<span><b>Hello</b>, world!</span>')

xml = fuze(xml1, xml2, prefer_slave_inner=True)
assert et.tostring(xml) == b'<span><b><i>Hello</i></b>, world!</span>'

xml = fuze(xml1, xml2, prefer_slave_inner=False)
assert et.tostring(xml) == b'<span><i><b>Hello</b></i>, world!</span>'
```

# Slave top-level tag is dropped
Note that top-level tag from slave is not merged. It is just dropped. If you want it to be merged into the output,
set `strip_slave_top_tag=False`.

# fuse() signature

```python
fuse(xml1, xml2, *, prefer_slave_inner=True, auto_segment=True, strip_slave_top_tag=True)
```
Where:
* `xml1` is the master XML document (LXML Element object, see http://lxml.de)
* `xml2` is the slave XML document
* `prefer_slave_inner` controls ambigiuty resolution
* `auto_segment` allows slave smarkup segmentation in case of conflicting markup
* `strip_slave_top_tag` allows `fuse` to ignore top-level tag from the slave XML

Returns fused XML document
