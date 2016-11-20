# XSL Coverage

[![PyPI version](https://badge.fury.io/py/xslcoverage.svg)](https://badge.fury.io/py/xslcoverage)

This project contains some python scripts and a Saxon plugin to be able to
compute the XSL Coverage of your XSL stylesheets. The coverage is given by HTML
files showing the coverage rates, and for each XSL stylesheet involved, the
covered lines, and what XML sources cover that line.

## Install the package
### Dependencies
The package depends on the following software:

* Saxon: this is the core XSLT used t process the stylesheets. Currently it
  works with Saxon 6.5.5, and Saxon-HE 9.7.x.
* Xerces2: contains some java archives used to be able to process XML documents
  using XInclude
* XML Resolver: java archive by Apache to resolve XML catalogs
* pygments: a python module used to display in HTML prettified source code

### Install Script
To install the package, use the standard python setup script provided. It
also supports the following specific install options, used to build the
classpath used when java runs saxon to process the stylesheets:

`--saxon-path`
:       Path where the saxon.jar archive is.

`--xerces-path`
:       Path where the xercesImpl.jar archive is. This archive is one of the
        archive provided by the Xerces2 bundle.

`--xml-resolver-path`
:       Path of the xml-resolver.jar provided by the Apache Fundation. Used
        to resolve catalogs.

When a path-option is not used the default path used to build the classpath 
is `/usr/share/java`.

Example:

```
$ python setup.py install --prefix=/path/to/install
                          --saxon-path=/usr/share/java/saxon-6.5.5
                          --xerces-path=/usr/share/java/xerces-2_11_0
```

## How to produce the coverage data
Once installed, several scripts are provided. What you can do:

### Using the raw Saxon XSLT wrapper
You can simply call **saxon-xslt2**, to replace the default saxon-xslt
script. It works like the original, except that it creates a trace file
containing the raw information of the XSL stylesheet lines processed, and
for which XML source.

The limitation is that it requires some manual additional steps to exploit the
traces later and compute the coverage.

### Using xslcoverage
The **xslcoverage** script is the main script to use. It contains two
subcommands:

`run [options] \<trace\_runner\> _runner__args_`
:       It call the plugin named _trace\_runner_ in charge to perform some
        XSLT processing (and maybe other things) and produce the trace files.

`report [options]`
:       It builds a coverage report in HTML format from trace files produced by
        a `run`.

The two subcommands can be combined but with care.

### xslcoverage to build coverage traces
Here are two examples:

1. Call **xslcoverage** and subcommand `run saxon` to run the saxon wrapper
   on your stylesheet(s) and output the trace file in a more consistent way.
   It calls the saxon-xslt2 wrapper of saxon, process the stylesheet(s) on your
   XML document, and it outputs some trace files that can be processed on the
   fly to compute the coverage, or that can be processed later. It produces a
   tracelog file containing all the necessary data needed for post-processing
   by the subcommand `report`.

   ```
   $ xslcoverage --trace-dir=/path/to/traces \
                 run saxon [saxon options] file.xml stylesheet.xsl
   ...
   Write traces to /path/to/traces/16312223507/trace-0001.xml
   ...
   Write Trace log '/path/to/traces/16312223507/tracelog.xml'
   ...
   ```

2. The package provides as an example a more sophisticated plugin that runs
   dblatex and produce coverage data. It works like the `saxon` plugin, except
   that it configures and calls dblatex the right way.
   ```
   $ xslcoverage --trace-dir=/path/to/traces \
                 run dblatex [dblatex options] document.xml
   ...
   Write traces to /path/to/traces/16312563508/trace-0001.xml
   ...
   Write Trace log '/path/to/traces/16312563508/tracelog.xml'
   ...
   ```

### xslcoverage to make a report from traces
Here are some examples:

3. To compute the coverage from existing trace files, call **xslcoverage**
   with the subcommand `report` on
   the tracelog file previously built by the `run` subcommand. It produces a
   bunch of HTML files of pretty printed XSL stylesheets with coverage
   information.
   ```
   $ xslcoverage report --from-log=/path/to/traces/16312223507/trace.log.xml \
                        --html-dir=/path/to/coverage-report
   ...
   /path/to/coverage-report/coverage_index.html
   ```

4. To compute the coverage from existing trace files without a tracelog file,
   you can simply specify the directory containing the trace files. The script
   will look for any XML file contained in the directory. The limitation is that
   it takes all the files, and does not discriminate from files produced by a
   coverage session or by another. Nevertheless, it can be an alternative to
   process trace files directly built by saxon-xslt2.
   ```
   $ xslcoverage --trace-dir=/path/to/traces/16312223507 \
                 report --html-dir=/path/to/coverage-report
   ...
   /path/to/coverage-report/coverage_index.html
   ```

5. You can also give an explicit list of trace files to compute. Note in this
   case that there is no more explicit directory where to output the HTML report
   files (so use the --html-dir option).
   ```
   $ xslcoverage report --html-dir=/path/to/coverage-report \
                        /path/to/traces/16312223507/trace-*.xml
   ...
   /path/to/coverage-report/coverage_index.html
   ```

### Making a report on the fly
You can mix the `run` and `report` subcommands, but the report must be set
first in the command line, because the run plugins pass all the next arguments
to the underlying tools in charge to actually process and build the trace files.

Note that when using `report` to build on the fly, some features are disabled
because meaningless:
* You cannot specify a tracelog file (it will the tracelog produced by the run)
* You cannot pass explicit trace files in the arguments (they will be
  interpreted as `run` parameters)

Here are some examples:

6. A basic report call mixed with a run. Without any options, the report is
   outputed in the directory containing the traces.
   ```
   $ xslcoverage --trace-dir=/path/to/traces \
                 report run saxon [saxon options] file.xml stylesheet.xsl
   ...
   Write traces to /path/to/traces/16312223507/trace-0001.xml
   ...
   Write Trace log '/path/to/traces/16312223507/tracelog.xml'
   ...
   /path/to/traces/16312223507/coverage_index.html
   ```

6. This report specifies the HTML directory, different from the trace
   directory.
   ```
   $ xslcoverage --trace-dir=/path/to/traces \
                 report --html-dir=/path/to/coverage-report \
                 run saxon [saxon options] file.xml stylesheet.xsl
   ...
   Write traces to /path/to/traces/16312223507/trace-0001.xml
   ...
   Write Trace log '/path/to/traces/16312223507/tracelog.xml'
   ...
   /path/to/coverage-report/coverage_index.html
   ```

## How to use the coverage data
The main HTML coverage file is called coverage\_index.html. Use your prefered
web browser to view it.
* It contains the list of the XSL file, and their computed coverage.
* There is a link to each XSL file, that gives which lines are covered or not
* For each line covered, clicking on them popup the list of the XML lines that
  originate the call of this XSL line.

## Example
See here an example of coverage:
[coverage\_index.html](https://marsgui.github.io/xslcoverage/example/traces/coverage_index.html "Coverage Example")

## Tool Extensibility
Currently **xslcoverage** only supports saxon, but you can define your own
runner through a dedicated plugin that will be loaded by the tool.

### Classes to Implement
To provide your own coverage runner, create a python plugin containing a
class named `TraceRunner` and optionnaly a class named `TraceParser`. The names
must be respected in order be loadable by xslcoverage.  The role of the classes
are:

   * **TraceRunner** is in charge to run the XSLT engine and produce the
     coverage traces.
   * **TraceParser** is in charge to parse the traces produced by TraceRunner,
     and to provide a coverage object. The coverage object must be derived from
     the XmlCoverFile class to be exploited to build the coverage report.

     If no TraceParser class is provided in the plugin, the default saxon parser
     is used to parse the trace files, assuming that the trace file format is
     the same.

### Classes Interfaces
The class must be compliant with the TraceRunnerBase and TraceParserBase
abstract interface defined in coverapi.py 


## Copyright
See the COPYRIGHT in the package.

