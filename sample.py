import lxml.etree as et
import lxmlx.event as ev

xml = et.fromstring('<a>Hello<?pi?> world!</a>')
print(et.tostring(ev.unscan(
    ev.scan(xml)
)))