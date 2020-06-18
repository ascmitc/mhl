from timeit import default_timer as timer

import lxml.builder
import lxml.etree as ET
from lxml import etree
from lxml import objectify
from lxml.builder import E


def parse():
    start = timer()
    # path = "/Users/sahm/temp/A002R2EC_2020-01-16_091500_0001.ascmhl"
    path = "/Users/sahm/temp/dummy_fs_2020-06-10_094406_0001.ascmhl"
    nsmap = {'mhl': 'http://theasc.com/ASCMHL'}
    for event, element in etree.iterparse(path, tag=('{http://theasc.com/ASCMHL}hash',)):
        # print(event, element.tag, element.text)
        # path = element.find('mhl:filename', namespaces=nsmap)
        # path = element.find('{http://theasc.com/ASCMHL}filename')
        # print(path.text)
        element.clear()

    end = timer()
    print(end - start)


def parse_no_ns():
    start = timer()
    path = "/Users/sahm/temp/dummy_fs_2020-06-10_094406_0001-no-ns.ascmhl"
    file = open(path, "rb")
    # tag=('hash', )
    for event, element in etree.iterparse(file, events=('start', 'end')):
        # path = element.find('filename')
        if event == 'start':
            pass
        else:
            if element.tag == 'filename':
                path = element
                # print(path.text)
            elif element.tag == 'hash':
                element.clear()
                while element.getprevious() is not None:
                    del element.getparent()[0]

    end = timer()
    print('parse no ns', end - start)
    print('end')


def parse_full():
    start = timer()
    path = "/Users/sahm/temp/dummy_fs_2020-06-10_094406_0001-no-ns.ascmhl"
    root = etree.parse(path).getroot()
    end = timer()
    print('parse no ns', end - start)
    print('end')


def write():
    with open('/tmp/test.txt', 'wb') as file:
        file.write(b'test\n')

    file2 = open('/tmp/test2.txt', 'wb')
    file2.write(b'test2\n')
    file2.flush()

    info_element = E.creatorinfo(
        E.host('asm-test'),
        E.tool('tool', version='2.0'),
    )

    print(etree.tostring(info_element, pretty_print=True, encoding="utf-8"))
    print()
    objectify.deannotate(info_element, cleanup_namespaces=True, xsi_nil=True)

    print(etree.tostring(info_element, pretty_print=True, encoding="utf-8"))


def schema():
    dbchangelog = 'http://www.host.org/xml/ns/dbchangelog'
    xsi = 'http://www.host.org/2001/XMLSchema-instance'
    E = lxml.builder.ElementMaker(
        nsmap={
            None: dbchangelog,
            'xsi': xsi})

    ROOT = E.databaseChangeLog
    DOC = E.include

    the_doc = ROOT()
    the_doc.attrib['{{{pre}}}schemaLocation'.format(pre=xsi)] = 'www.host.org/xml/ns/dbchangelog'

    print(ET.tostring(the_doc,
                      pretty_print=True, xml_declaration=True, encoding='utf-8'))


# parse()
# parse_no_ns()
# parse_full()

write()
