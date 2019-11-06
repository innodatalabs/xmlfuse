from types import SimpleNamespace
import lxmlx.event as ev
from lxmlx.event import ENTER, EXIT, TEXT, PI, COMMENT

SPOT = 'spot'  # internal event type to mark various zero-length markup


def fuse(xml1, xml2, auto_segment=True, prefer_slave_inner=True, strip_slave_top_tag=True):
    nsmap = xml2.nsmap or {}
    nsmap.update(xml1.nsmap or {})

    xml1 = list(ev.scan(xml1))
    xml2 = list(ev.scan(xml2))

    if strip_slave_top_tag:
        _, *xml2, _ = xml2

    events = fuse_events(xml1, xml2, prefer_slave_inner=prefer_slave_inner, auto_segment=auto_segment)
    return ev.unscan(events, nsmap=nsmap)

def fuse_events(events1, events2, auto_segment=True, prefer_slave_inner=True):
    events1 = list(events1)
    events2 = list(events2)

    if ev.text_of(events1) != ev.text_of(events2):
        raise_text_diff(ev.text_of(events1), ev.text_of(events2))

    offsets = text_offsets(events1) | text_offsets(events2)

    events1 = list(segment_text(events1, offsets))
    events2 = list(segment_text(events2, offsets))

    events = analyze(events1, events2, prefer_slave_inner=prefer_slave_inner, auto_segment=auto_segment)

    return events


def raise_text_diff(t1, t2):
    for offset,(c1,c2) in enumerate(zip(t1, t2)):
        if c1 != c2:
            snippet1 = t1[max(0, offset-20):offset + 20]
            snippet2 = t2[max(0, offset-20):offset + 20]
            raise RuntimeError('Input documents have different text at offset %s:\n'
                % offset + snippet1 + '\n' + snippet2)
    offset = min(len(t1), len(t2))
    snippet1 = t1[max(0, offset-20):offset + 20]
    snippet2 = t2[max(0, offset-20):offset + 20]
    if len(t1) > len(t2):
        raise RuntimeError('Master document has longer text than the slave:\n'
                + snippet1 + '\n' + snippet2)
    elif len(t1) < len(t2):
        raise RuntimeError('Master document has shorter text than the slave:\n'
                + snippet1 + '\n' + snippet2)
    assert False

def text_offsets(events):
    offsets = set()
    offset = 0
    for e in events:
        if e['type'] == TEXT:
            offsets.add(offset)
            offset += len(e['text'])
    offsets.add(offset)

    return offsets


def segment_text(events, offsets):
    '''Segments text according to the offsets'''
    offsets = sorted(offsets, reverse=True)
    if offsets and offsets[-1] == 0:
        offsets.pop()

    offset = 0
    for e in events:
        if e['type'] == TEXT:
            text = e['text']
            length = len(text)
            while offsets and offsets[-1] - offset < length:
                o = offsets.pop() - offset
                yield dict(type=TEXT, text=text[:o])
                text = text[o:]
                offset += o
                length -= o
            yield dict(type=TEXT, text=text)
            offset += len(text)
            if offsets and offsets[-1] == offset:
                offsets.pop()
        else:
            yield e


class Token:
    def __init__(self, prefix=None, text=None, suffix=None):
        self.prefix = prefix or []
        self.text = text
        self.suffix = suffix or []

    def normalized(self):
        prefix = list(reversed(list(normalize_prefix(self.prefix))))
        return Token(prefix, self.text, self.suffix)

    def __repr__(self):
        return repr(dict(prefix=self.prefix, text=self.text, suffix=self.suffix))

    def __eq__(self, other):
        if self is other:
            return True
        if self.__class__ is not other.__class__:
            return False
        return self.prefix == other.prefix and self.text == other.text and self.suffix == other.suffix


def normalize_prefix(prefix):
    # clamp together opening and closing tags of a zero-length elts

    out = []
    stack = []
    for e in reversed(prefix):
        if e['type'] == EXIT:
            stack.append(e)  # delay decision - may have ENTER coming
        elif e['type'] == ENTER:
            if stack:
                out.insert(0, e)
                out.append(stack.pop())
            else:
                if out:
                    yield dict(type=SPOT, spot=out[:])
                    out.clear()
                yield e
        else:
            assert e['type'] in (PI, COMMENT)
            out.append(e)
    if out:
        yield dict(type=SPOT, spot=out[:])


def as_token_stream(events):
    '''
    Represents XML stream as a sequence of "tokens".
    Each token has text, prefix and suffix.

    prefix is a list of opening XML tags (that open before the text), and, zero-length XML tags. Prefix list can be empty.
    suffix is a list of closing XML tags (that close immedeately after this text).

    For example, the following XML snippet:

        Hello, <br/><i>world!</i>

    may have the following token stream representation:

        (text="Hello, ", prefix=[], suffix=[]),
        (text="world!", prefix=[<br/>, <i>], suffix=[</i>])
    '''

    token = Token()
    for e,p in ev.with_peer(events):
        if e['type'] == ENTER:
            if token.text:
                yield token.normalized()
                token = Token()
            token.prefix.append(e)
        elif e['type'] == EXIT:
            if not token.text:
                # zero-length thing. Leave as prefix
                token.prefix.append(dict(type=ev.EXIT, peer=p))
            else:
                token.suffix.append(dict(type=ev.EXIT, peer=p))
        elif e['type'] == TEXT:
            if token.text:
                yield token.normalized()
                token = Token()
            token.text = e['text']
        elif e['type'] in (COMMENT, PI):
            if token.text:
                yield token.normalized()
                token = Token()
            token.prefix.append(e)
        else:
            assert False, e

    if token.text:
        yield token.normalized()


def analyze(events1, events2, prefer_slave_inner=True, auto_segment=True):
    # for convenience of synchronizing by text, lets convert XML streams to
    # token representation
    sync = []
    for master, slave in zip(as_token_stream(events1), as_token_stream(events2)):
        assert master.text == slave.text, (master, slave)
        sync.append(SimpleNamespace(
            master=master, slave=slave,
            text=master.text,
            prefix=[],
            suffix=[],
        ))

    def local_reduce(prefix, suffix, out_prefix, out_suffix):
        while prefix:
            if prefix[-1]['type'] == SPOT:
                out_prefix.insert(0, prefix.pop())
                continue
            if not suffix:
                break
            x = prefix.pop()
            assert x['type'] == ENTER
            out_prefix.insert(0, x)
            y = suffix.pop(0)
            assert y['type'] == EXIT
            assert y['peer'] is x
            out_suffix.append(y)

    def helper(index):
        for i in range(index):
            m = sync[i].master
            s = sync[i].slave
            assert len(m.suffix) == 0 and len(s.suffix) == 0

        h = sync[index]
        for i in reversed(range(index+1)):
            l = sync[i]

            if prefer_slave_inner:
                local_reduce(l.slave.prefix, h.slave.suffix, l.prefix, h.suffix)
                local_reduce(l.master.prefix, h.master.suffix, l.prefix, h.suffix)
            else:
                local_reduce(l.master.prefix, h.master.suffix, l.prefix, h.suffix)
                local_reduce(l.slave.prefix, h.slave.suffix, l.prefix, h.suffix)

            if len(h.master.suffix) == 0 and len(h.slave.suffix) == 0:
                return  # reached our invariant, done helper

            if len(l.master.prefix) == 0 and len(l.slave.prefix) == 0:
                continue  # match with earlier tags

            # here we have a conflict
            if not auto_segment:
                o = l.master.prefix[-1] if l.master.prefix else l.slave.prefix[-1]
                c = h.master.suffix[0] if h.master.suffix else h.slave.suffix[0]
                raise RuntimeError('Conflicting markup: <%s> just before "%s" and </%s> just after "%s"'
                    % (o['tag'], l.text, c['peer']['tag'], h.text))

            if l.master.prefix:
                assert not l.slave.prefix
                assert not h.master.suffix
                assert h.slave.suffix
                # close slave on previous step and re-open here

                sync[i-1].slave.suffix.extend(h.slave.suffix)
                for e in reversed(h.slave.suffix):
                    l.prefix.append(e['peer'])
                h.suffix.extend(h.slave.suffix)
                h.slave.suffix.clear()
                for j in reversed(range(i)):
                    local_reduce(sync[j].slave.prefix, sync[i-1].slave.suffix, sync[j].prefix, sync[i-1].suffix)
                    if not sync[i-1].slave.suffix:
                        break
            else:
                assert l.slave.prefix
                assert not h.slave.suffix
                assert h.master.suffix

                # close slave here and re-open on the right
                l.prefix.extend(l.slave.prefix)
                for e in reversed(l.slave.prefix):
                    h.suffix.append(dict(type=EXIT, peer=e))
                sync[index+1].slave.prefix.extend(l.slave.prefix)
                l.slave.prefix.clear()
                for j in reversed(range(i)):
                    rc = local_reduce(sync[j].master.prefix, sync[i].master.suffix, sync[j].prefix, sync[i].suffix)
                    if not sync[i].master.suffix:
                        break
                return

    for index in range(len(sync)):
        helper(index)

    stack = []
    for t in sync:
        for e in t.prefix:
            if e['type'] == SPOT:
                yield from e['spot']
            else:
                assert e['type'] == ENTER
                stack.append(e)
                yield e

        yield dict(type=TEXT, text=t.text)

        for e in t.suffix:
            assert e['type'] == EXIT
            assert e['peer'] is stack[-1]
            stack.pop()
            yield dict(type=EXIT)

