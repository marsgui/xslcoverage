# XSL Coverage
This project contains some python scripts and a Saxon plugin to be able to
compute the XSL Coverage of your XSL stylesheets.

## How to produce the coverage data
1. Compile the xslcover.jar archive to use with Saxon. The java code works with
   saxon 6.5.5.

      $ make jar

2. Call runcover to run XSLT on your stylesheet(s). It calls the saxon-xslt2.py
   wrapper of saxon, process the stylesheet(s) on your XML document, and it
   outputs some trace files that can be processed on the fly to compute the
   coverage, or that can be processed later.

      $ python runcover.py file.xml stylesheet.xsl
      ...

3. To compute the coverage, call xmlcover on the tracelog file built by
   runcover.py. It produces a bunch of HTML files of pretty printed XSL
   stylesheets with coverage information.

      $ python xmlcover.py --from-log=/path/to/traces/trace.log.xml \
                           --html-dir=/path/to/coverage-report
      ...

## How to use the coverage data
The main HTML coverage file is called coverage\_index.html. Use your prefered
web browser to view it.
* It contains the list of the XSL file, the computed
* There is a link to each XSL file, that gives which lines are covered or not
* For each line covered, clicking on them popup the list of the XML lines that
  originate the call of this XSL line.

coverage
