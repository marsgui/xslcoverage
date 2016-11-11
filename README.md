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
  works with Saxon 6.5.5.
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

1. You can simply call saxon-xslt2, to replace the default saxon-xslt script.
   It works like the original, except that it creates a trace file containing
   the raw information of the XSL stylesheet line processed, and for which XML
   source.

2. Instead, you can also call runcover to run XSLT on your stylesheet(s) and
   output the trace file in a more consistent way. It calls the saxon-xslt2
   wrapper of saxon, process the stylesheet(s) on your XML document, and it
   outputs some trace files that can be processed on the fly to compute the
   coverage, or that can be processed later. It produces a tracelog file
   containing all the necessary data needed for post-processing by xmlcover.

   ```
   $ runcover --trace-dir=/path/to/traces [saxon options] \
              file.xml stylesheet.xsl
   ...
   Write traces to /path/to/traces/16312223507/trace-0001.xml
   ...
   Write Trace log '/path/to/traces/16312223507/tracelog.xml'
   ...
   ```

3. To compute the coverage from existing trace files, call xmlcover on the
   tracelog file built by runcover. It produces a bunch of HTML files of
   pretty printed XSL stylesheets with coverage information.

   ```
   $ xmlcover --from-log=/path/to/traces/16312223507/trace.log.xml \
              --html-dir=/path/to/coverage-report
   ...
   /path/to/coverage-report/coverage_index.html
   ```

4. The package provides as an example a more sophisticated wrapper to call
   dblatex and produce coverage data. It works like runcover, except that
   it configures and calls dblatex the right way.
   ```
   $ dbcover --trace-dir=/path/to/traces --report [dblatex options] document.xml
   ...
   Write traces to /path/to/traces/16312563508/trace-0001.xml
   ...
   Write Trace log '/path/to/traces/16312563508/tracelog.xml'
   ...
   /path/to/traces/16312563508/coverage_index.html
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

## Copyright
See the COPYRIGHT in the package.

