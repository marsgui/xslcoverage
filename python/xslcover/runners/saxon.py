#
# XSL Coverage - See COPYRIGHT
#
import os
from subprocess import Popen
from xslcover import config 
from xslcover.saxontrace import SaxonParser
from xslcover.coverapi import TraceRunnerBase

def create_trace_filename(dirname, max_files=1000):
    filename_candidate = ""
    for i in range(1, max_files):
        filename_candidate = os.path.join(dirname, "trace-%04d.xml" % i)
        if not(os.path.exists(filename_candidate)):
            break
    return filename_candidate

class SaxonRunner(TraceRunnerBase):
    """
    Extend the default saxon 6.5.5 script to have:
    - Catalog resolver (xml-resolver required)
    - XInclude support (xercesImpl required)
    - Tracing of data to compute coverage (xslcover required)
    """
    _classpath = ":".join(["%(saxon_path)s/saxon.jar",
                           "%(xml_resolver_path)s/xml-resolver.jar",
                           "/etc/xml/resolver",
                           "%(xerces_path)s/xercesImpl.jar",
                           "%(xslcover_path)s/xslcover-saxon.jar"])

    def __init__(self):
        java_paths = {}
        for path_key in ("saxon_path", "xml_resolver_path", "xerces_path",
                         "xslcover_path"):
            java_paths[path_key] = config.get_value(path_key, "/usr/share/java")
        self.classpath = self._classpath % java_paths

        self.cmd = ["java", "-classpath", self.classpath,
           "-Dorg.apache.xerces.xni.parser.XMLParserConfiguration=org.apache.xerces.parsers.XIncludeParserConfiguration",
           "com.icl.saxon.StyleSheet",
           "-TL", "xslcover.icl.saxon.trace.XslcoverTraceListenerV65",
           "-x", "org.apache.xml.resolver.tools.ResolvingXMLReader",
           "-y", "org.apache.xml.resolver.tools.ResolvingXMLReader",
           "-r", "org.apache.xml.resolver.tools.CatalogResolver"]

    def trace_generator(self):
        name = os.path.splitext(os.path.basename(__file__))[0]
        return name

    def run(self, args, trace_dir="", trace_filename=""):
        if not(trace_filename):
            trace_filename = create_trace_filename(trace_dir)

        if trace_filename:
            print "Write traces to %s" % trace_filename
            env = {}
            env.update(os.environ)
            env.update({ "TRACE_FILE": trace_filename })
        else:
            env = None

        self.cmd += args
        p = Popen(self.cmd, env=env)
        rc = p.wait()
        return rc


class TraceRunner(SaxonRunner):
    "Plugin Class to load"

class TraceParser(SaxonParser):
    "Plugin Class to load"

