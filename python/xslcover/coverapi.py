import os
from abc import ABCMeta, abstractmethod

class TraceParserBase:
    """
    Object in charge to parse one or more trace files, and build the coverage
    objects derived from XmlCoverFileBase, containing all the needed coverage
    information to make a coverage report.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def read_trace(self, trace_file):
        """
        Parse a trace file. The method is to call for each trace file
        produced by a coverage session.
        """
        pass

    @abstractmethod
    def get_coverages(self):
        """
        Return an array of the coverage objects, derived XmlCoverFileBase,
        built from the trace files read. When the method is called, it is
        assumed that the sequence of trace reads is finished.
        """
        pass


class TraceRunnerBase:
    """
    Wrapper of the command that will call the XSLT and adapt it to produce some
    trace files.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def trace_generator(self):
        """
        Return the name of the trace generator. Typically it is the name of
        the plugin containing the TraceRunner class, because this plugin usually
        contains also the TraceParser used later to make the coverage report.
        """
        name = os.path.splitext(os.path.basename(__file__))[0]
        return name

    @abstractmethod
    def run(self, args, trace_dir="", **kargs):
        """
        Run the command that calls the XSLT and produce the trace files.
        The command arguments aregiven by <args>, and one can specify
        a trace directory where to store the traces.
        """
        pass


class XmlCoverFileBase:
    """
    Object containing the coverage information about an XSL file used during
    the transformation process initiated by a TraceRunner
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def line_status(self, linenum):
        """
        Return the coverage status of the line <linenum> of the XSL file
        The status can be:
        * 'covered': line processed by XSLT
        * 'uncovered': line non processed by XSLT
        * 'unused': line not subject to processing, like comments
        """
        pass

    @abstractmethod
    def content_string(self):
        """
        Return as a string the content of the XSL file analyzed
        """
        pass

    @abstractmethod
    def filepath(self):
        """
        Path of the XSL File analyzed
        """
        pass

    @abstractmethod
    def covering_files(self):
        """
        Iterator that returns a tuple (linenum, XML lines). The XML lines
        are the lines of XML sources that have been transformed by the
        <linenum> XSL instruction. The XML lines are a list of
        'XML_source_path:XML_source_linenum'.
        """
        pass

