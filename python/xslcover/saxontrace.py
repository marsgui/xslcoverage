#
# XSL Coverage - See COPYRIGHT
#
import os
import re
import xml.etree.ElementTree as ET
from coverfile import XmlCoverFile
from coverapi import TraceParserBase


class Position:
    def __init__(self, bufpos, linepos):
        self.position(bufpos, linepos)

    def position(self, bufpos, linepos):
        self.bufpos = bufpos
        self.linepos = linepos

class ElementZone:
    def __init__(self, tag, parent=None):
        self.start = Position(0,0)
        self.end = Position(0,0)
        self.tag = tag
        self.empty = False
        self.parent = parent
        self.children = []

    def add_child(self, child):
        self.children.append(child)
        child.parent = self

class ElementList:
    def __init__(self):
        self.starting = []
        self.ending = []


class TreeLineBuilder:
    """
    Build an XML Element Tree from source, where each element registers its
    position in the source file (line and offset from the beginning of the
    file).
    """
    tag_pattern = "((\w+:)?(%s))"

    def __init__(self, databuf):
        self.tag_stack = []
        self.tag_zones = []
        self.tag_lines = {}
        self.databuf = databuf
        self.datapos = Position(0,1) # First line is '1'
        self.depth = 0

    def _abs_from(self, new_pos):
        abs_pos = self.datapos.bufpos + new_pos
        buf = self.databuf[self.datapos.bufpos:abs_pos]
        lines = buf.split("\n")
        abs_line = self.datapos.linepos + len(lines) -1
        return (abs_pos, abs_line)

    def _new_element(self, tag):
        e = ElementZone(tag)
        if self.tag_stack:
            p = self.tag_stack[-1]
            p.add_child(e)
        self.tag_stack.append(e)
        self.tag_zones.append(e)
        return e

    def _set_starting_line(self, e):
        l = self.tag_lines.get(e.start.linepos, ElementList())
        l.starting.append(e)
        self.tag_lines[e.start.linepos] = l

    def _set_ending_line(self, e):
        l = self.tag_lines.get(e.end.linepos, ElementList())
        l.ending.append(e)
        self.tag_lines[e.end.linepos] = l

    def _split_xmlns(self, tag):
        m = re.match("{([^}]+)}(.*)", tag)
        if m:
            return m.group(1), m.group(2)
        else:
            return "", tag

    def start(self, tag, attrib):   # Called for each opening tag.
        buf = self.databuf[self.datapos.bufpos:]

        xmlns, tag = self._split_xmlns(tag)

        m = re.search("<"+self.tag_pattern % tag, buf)
        if not(m):
            print "%s => '%s'" % (tag, buf)
        fulltag = m.group(1)
        abs_pos, abs_line = self._abs_from(m.start())
        e = self._new_element(fulltag)
        e.start.position(abs_pos, abs_line)
        self._set_starting_line(e)
        self.datapos.position(abs_pos, abs_line)
        self.depth += 1

    def end(self, tag):             # Called for each closing tag.
        buf = self.databuf[self.datapos.bufpos:]
        xmlns, tag = self._split_xmlns(tag)
        m1 = re.search("</"+self.tag_pattern % tag+"\s*>", buf)
        m2 = re.search("<"+self.tag_pattern % tag+"(\s.*?)?/>",
                          buf, re.M|re.DOTALL)
        if not(m1 and m2):
            m = m1 or m2
        elif m1.end() < m2.end():
            m = m1
        else:
            m = m2
        #if not(m):
        #    m = re.search("<"+self.tag_pattern % tag+"/>", buf)
        abs_pos, abs_line = self._abs_from(m.end())
        fulltag = m.group(1)
        e = self.tag_stack[-1]
        e.end.position(abs_pos, abs_line)
        if m == m2: e.empty = True
        self._set_ending_line(e)
        self.datapos.position(abs_pos, abs_line)
        self.depth -= 1
        self.tag_stack.remove(e)

    def data(self, data):
        pass

    def close(self):    # Called when all data has been parsed.
        pass


class SaxonCoverFile(XmlCoverFile):
    """
    Adapt the base coverage file, to make coverage done by saxon more accurate
    by fixing some missing covered lines.
    """
    def __init__(self, xslfile):
        self.xslfile = xslfile
        self.tree_builder = TreeLineBuilder("".join(xslfile.content))
        XmlCoverFile.__init__(self, xslfile)

    def _fix_multiline_empty_tag(self, linenum, elements):
        # If the last line of an empty tag like this is covered then all the
        # lines of the tag are covered:
        #
        #   <tag foo="bar"
        #        other="baz"
        #        read="write"/>
        #
        if self.line_status(linenum) != "covered":
            return False

        for e in elements.ending:
            if (e.empty and e.start.linepos < e.end.linepos):
                for i in range(e.start.linepos, e.end.linepos):
                    if self.line_status(i) != "covered":
                        line_st = self.xslfile.getline(i)
                        line_st.cover_fragment("empty filled", None)
        return True

    def _fix_closing_tag(self, linenum, elements):
        # If an opening tag is covered, then the closing tag is covered too
        end_of_covered = [e for e in elements.ending \
                          if self.line_status(e.start.linepos) == "covered"]

        # If all the tags on the line are covered, the whole line is
        # covered
        if len(end_of_covered) == len(elements.ending):
            line_end = self.xslfile.getline(linenum)
            line_end.cover_fragment("end keyword", None)
            return True

    def _fix_withparam_tag(self, linenum, elements):
        # Cover the <xsl:with-param ... /> elements when it is inside a covered
        # template call
        if self.line_status(linenum) != "covered":
            return False

        fixed = False
        for e in elements.starting:
            if not("call-template" in e.tag or "apply-templates" in e.tag):
                continue
            for child in e.children:
                if ("with-param" in child.tag) and child.empty:
                    for i in range(child.start.linepos, child.end.linepos+1):
                        if self.line_status(i) != "covered":
                            line_st = self.xslfile.getline(i)
                            line_st.cover_fragment("in template call", None)
                            fixed = True
        return fixed

    def fix_coverage(self):
        parser = ET.XMLParser(target=self.tree_builder)
        parser.feed(self.tree_builder.databuf)
        parser.close()
        for linenum, elements in self.tree_builder.tag_lines.items():
            if elements.ending and not(elements.starting):
                if self._fix_multiline_empty_tag(linenum, elements):
                    continue
                if self._fix_closing_tag(linenum, elements):
                    continue
            elif self._fix_withparam_tag(linenum, elements):
                continue


class Line:
    def __init__(self, fileobj, linenum, content=""):
        self.fileobj = fileobj
        self.linenum = linenum
        self.covered_fragments = []
        self.content = content

    def cover_fragment(self, fragment, source):
        self.covered_fragments.append((fragment, source))

    def __cmp__(self, other):
        return cmp(self.linenum, other.linenum)


class CoverFileData:
    def __init__(self, filepath=""):
        self.filepath = filepath
        self._trash_line = Line(self, -1)
        self.lines = {}
        if self.filepath:
            self.content = open(self.filepath).readlines()
        else:
            self.content = []

    def getline(self, linestr):
        try:
            linenum = int(linestr)
            lineobj = self.lines.get(linenum, None)
            if not(lineobj):
                lineobj = Line(self, linenum, self.content[linenum-1])
                self.lines[linenum] = lineobj
        except:
            lineobj = self._trash_line
        return lineobj


class XslFile(CoverFileData):
    pass

class XmlFile(CoverFileData):
    pass

class FileManager:
    def __init__(self, file_type):
        self.file_type = file_type
        self.files = {}
        self._trash_file = file_type()

    def get_or_create(self, filepath):
        #print self.files, filepath
        _file = self.files.get(filepath, None)
        if not(_file):
            if os.path.isfile(filepath):
                _file = self.file_type(filepath)
                self.files[filepath] = _file
            else:
                _file = self._trash_file
        return _file


class SaxonParser(TraceParserBase):
    """
    Parse the trace files produced by Saxon, and create the coverage files
    """
    def __init__(self):
        self.coverfile_cls = SaxonCoverFile
        self.xslfiles = FileManager(XslFile)
        self.xmlfiles = FileManager(XmlFile)
        self.traces = []
        self.coverages = []

    def read_trace(self, xmlfilename):
        document = ET.parse(xmlfilename)
        self.traces.append(document)
        root = document.getroot()
        self._parse_children(root, None)

    def get_coverages(self):
        if not(self.coverages):
            for xslfile in self.xslfiles.files.values():
                xcover = self.coverfile_cls(xslfile)
                self.coverages.append(xcover)
            self.stats_done = True
        return self.coverages

    def _parse_children(self, node, source):
        for child in node:
            if child.tag == "stylesheet":
                #print source
                self._process_stylesheet(child, source)
            elif child.tag == "source":
                self._process_source(child)

    def _process_stylesheet(self, xslnode, source):
        xslfile = self.getxsl(xslnode.get("file").replace("file:",""))
        line = xslfile.getline(xslnode.get("line"))
        line.cover_fragment(xslnode.get("element"), source)
        self._parse_children(xslnode, source)

    def _process_source(self, xmlnode):
        xmlfile = self.getxml(xmlnode.get("file").replace("file:",""))
        source = xmlfile.getline(xmlnode.get("line"))
        self._parse_children(xmlnode, source)

    def getxsl(self, filename):
        return self.xslfiles.get_or_create(filename)

    def getxml(self, filename):
        return self.xmlfiles.get_or_create(filename)

