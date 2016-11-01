#!/usr/bin/env python
import os
from subprocess import Popen

class TraceSaxon:
    """
    Extend the default saxon script to have:
    - Catalog resolver (xml-resolver required)
    - XInclude support (xercesImpl required)
    - Tracing of data to compute coverage (xmlcover required)
    """
    classpath = ":".join(["/usr/share/java/saxon.jar",
                          "/usr/share/java/xml-resolver.jar",
                          "/etc/xml/resolver",
                          "/home/ben/manip/saxon/xerces-2_11_0/xercesImpl.jar",
                          "/home/ben/manip/saxon/dbcover.jar"])

    cmd = ["java", "-classpath", classpath,
           "-Dorg.apache.xerces.xni.parser.XMLParserConfiguration=org.apache.xerces.parsers.XIncludeParserConfiguration",
           "com.icl.saxon.StyleSheet",
           "-TL", "dblatex.saxon.trace.TimedTraceListener",
           "-x", "org.apache.xml.resolver.tools.ResolvingXMLReader",
           "-y", "org.apache.xml.resolver.tools.ResolvingXMLReader",
           "-r", "org.apache.xml.resolver.tools.CatalogResolver"]

    def __init__(self):
        pass

    def run(self, args, trace_filename=""):
        if trace_filename:
            print "Write traces to %s" % trace_filename
            env = {}
            env.update(os.environ)
            env.update({ "TRACE_FILE": trace_filename })
        else:
            env = None

        p = Popen(self.cmd + args, env=env)
        rc = p.wait()
        return rc


def create_trace_filename(dirname, max_files=1000):
    filename_candidate = ""
    for i in range(1, max_files):
        filename_candidate = os.path.join(dirname, "trace-%04d.xml" % i)
        if not(os.path.exists(filename_candidate)):
            break
    return filename_candidate


def main():
    import sys
    from argparse import ArgumentParser
    parser = ArgumentParser(description='XSLT engine with traces')
    parser.add_argument("-D", "--trace-dir",
          help="Directory containing the traces")

    options, remain_args =  parser.parse_known_args()

    if not(options.trace_dir):
        options.trace_dir = os.environ.get("TRACE_DIRECTORY", "")

    trace_filename = create_trace_filename(options.trace_dir)

    s = TraceSaxon()
    rc = s.run(remain_args, trace_filename=trace_filename)
    sys.exit(rc)
 

if __name__ == "__main__":
    main()
