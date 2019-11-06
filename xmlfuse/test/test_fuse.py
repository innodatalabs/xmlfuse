import lxml.etree as et
import lxmlx.event as ev
from xmlfuse.fuse import text_offsets, segment_text, as_token_stream, Token, fuse
import pytest

def test_01():
    xml = et.fromstring('<a>Hello, <i>bright</i> <b>world</b></a>')

    offsets = text_offsets(ev.scan(xml))
    assert offsets == {0, 7, 13, 14, 19}

def test_02():
    xml = et.fromstring('<a>Hello, <i>bright</i> <b>world</b></a>')

    segments = [e['text'] for e in segment_text(ev.scan(xml), {0, 2, 8}) if e['type'] == ev.TEXT]
    assert segments == ['He', 'llo, ', 'b', 'right', ' ', 'world']

def test_03():
    xml = et.fromstring('<a>Hello, <i><s>bright</s></i> <b>world</b></a>')

    tokens = list(as_token_stream(ev.scan(xml)))
    a = dict(type=ev.ENTER, tag='a')
    i = dict(type=ev.ENTER, tag='i')
    s = dict(type=ev.ENTER, tag='s')
    b = dict(type=ev.ENTER, tag='b')
    assert tokens == [
        Token(prefix=[a], text='Hello, '),
        Token(prefix=[i, s], text='bright', suffix=[dict(type=ev.EXIT, peer=s), dict(type=ev.EXIT, peer=i)]),
        Token(text=' '),
        Token(prefix=[b], text='world', suffix=[dict(type=ev.EXIT, peer=b), dict(type=ev.EXIT, peer=a)])
    ]


def test_03a():
    xml = et.fromstring('<a>Hello, bright<br/> <b>world</b></a>')

    tokens = list(as_token_stream(ev.scan(xml)))
    a = dict(type=ev.ENTER, tag='a')
    a_ = dict(type=ev.EXIT, peer=a)
    b = dict(type=ev.ENTER, tag='b')
    b_ = dict(type=ev.EXIT, peer=b)
    br = dict(type=ev.ENTER, tag='br')
    br_ = dict(type=ev.EXIT, peer=br)
    assert tokens == [
        Token(prefix=[a], text='Hello, bright'),
        Token(prefix=[{'type': 'spot', 'spot': [br, br_]}], text=' '),
        Token(prefix=[b], text='world', suffix=[b_, a_])
    ]

def test_05():
    xml1 = et.fromstring('<a><b>Hello</b>, world</a>')
    xml2 = et.fromstring('<a>Hello, <i>world</i></a>')

    merged = fuse(xml1, xml2)
    result = et.tostring(merged)

    model = b'<a><b>Hello</b>, <i>world</i></a>'
    if model != result:
        print(model)
        print(result)
        assert False

def test_06():
    xml1 = et.fromstring('<a><b>Hello, </b>world</a>')
    xml2 = et.fromstring('<a>Hello, <i>world</i></a>')

    merged = fuse(xml1, xml2)
    result = et.tostring(merged)

    model = b'<a><b>Hello, </b><i>world</i></a>'
    if model != result:
        print(model)
        print(result)
        assert False

def test_07():
    xml1 = et.fromstring('<a><b>Hello, w</b>orld</a>')
    xml2 = et.fromstring('<a>Hello, <i>world</i></a>')

    merged = fuse(xml1, xml2)
    result = et.tostring(merged)

    model = b'<a><b>Hello, <i>w</i></b><i>orld</i></a>'
    if model != result:
        print(model)
        print(result)
        assert False

def test_08():
    xml1 = et.fromstring('<a><b>Hello</b>, <b>world</b></a>')
    xml2 = et.fromstring('<a>Hello, <i>worl</i>d</a>')

    merged = fuse(xml1, xml2)
    result = et.tostring(merged)

    model = b'<a><b>Hello</b>, <b><i>worl</i>d</b></a>'
    if model != result:
        print(model)
        print(result)
        assert False

def test_09():
    xml1 = et.fromstring('<a><b>Hello</b>, w<b>orld</b></a>')
    xml2 = et.fromstring('<a>Hello, <i>worl</i>d</a>')

    merged = fuse(xml1, xml2)
    result = et.tostring(merged)

    model = b'<a><b>Hello</b>, <i>w</i><b><i>orl</i>d</b></a>'
    if model != result:
        print(model)
        print(result)
        assert False


def test_10():
    xml1 = et.fromstring('<a><b>Hello</b>,<br/> world</a>')
    xml2 = et.fromstring('<a>Hello, <i>world</i></a>')

    merged = fuse(xml1, xml2)
    result = et.tostring(merged)

    model = b'<a><b>Hello</b>,<br/> <i>world</i></a>'
    if model != result:
        print(model)
        print(result)
        assert False


def test_11():
    xml1 = et.fromstring('<a><b>Hello</b>,<br/> world</a>')
    xml2 = et.fromstring('<a><br><img/></br>Hello, <i>world</i></a>')

    merged = fuse(xml1, xml2)
    result = et.tostring(merged)

    model = b'<a><b><br><img/></br>Hello</b>,<br/> <i>world</i></a>'
    if model != result:
        print(model)
        print(result)
        assert False


def test_12():
    xml1 = et.fromstring('<a><b>Hello</b>,<br/> world</a>')
    xml2 = et.fromstring('<a><br><img/></br><i>Hello</i>, <i>world</i></a>')

    merged = fuse(xml1, xml2, prefer_slave_inner=False)
    result = et.tostring(merged)

    model = b'<a><br><img/></br><i><b>Hello</b></i>,<br/> <i>world</i></a>'
    if model != result:
        print(model)
        print(result)
        assert False


def test_13():
    xml1 = et.fromstring('<a><b>Hello</b>, world</a>')
    xml2 = et.fromstring('<a>Hello,<?pi ?> <i>world</i></a>')

    merged = fuse(xml1, xml2, prefer_slave_inner=False)
    result = et.tostring(merged)

    model = b'<a><b>Hello</b>,<?pi ?> <i>world</i></a>'
    if model != result:
        print(model)
        print(result)
        assert False


def test_14():
    xml1 = et.fromstring('<a><b>Hello</b>, world</a>')
    xml2 = et.fromstring('<a>Hello,<!-- Hey Jude! --> <i>world</i></a>')

    merged = fuse(xml1, xml2, prefer_slave_inner=False)
    result = et.tostring(merged)

    model = b'<a><b>Hello</b>,<!-- Hey Jude! --> <i>world</i></a>'
    if model != result:
        print(model)
        print(result)
        assert False


def test_15():
    xml1 = et.fromstring('<a><b>12345</b>67890</a>')
    xml2 = et.fromstring('<a>123<i>4567890</i></a>')

    with pytest.raises(RuntimeError, match="Conflicting markup"):
        fuse(xml1, xml2, prefer_slave_inner=False, auto_segment=False)


def test_16():
    xml1 = et.fromstring('<a>Hello and Bye</a>')
    xml2 = et.fromstring('<a>Hello and Good bye!</a>')

    with pytest.raises(RuntimeError, match="Input documents have different text at offset 10"):
        fuse(xml1, xml2, prefer_slave_inner=False, auto_segment=False)

def test_17():
    xml1 = et.fromstring('<a>Hello and</a>')
    xml2 = et.fromstring('<a>Hello and Good bye!</a>')

    with pytest.raises(RuntimeError, match="Master document has shorter text than the slave.*"):
        fuse(xml1, xml2, prefer_slave_inner=False, auto_segment=False)

def test_18():
    xml1 = et.fromstring('<a>Hello and Good bye!</a>')
    xml2 = et.fromstring('<a>Hello and</a>')

    with pytest.raises(RuntimeError, match="Master document has longer text than the slave.*"):
        fuse(xml1, xml2, prefer_slave_inner=False, auto_segment=False)
