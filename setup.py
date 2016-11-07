#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
# xslcoverage python setup script - See the COPYRIGHT
#
import os
import sys
import re
import glob
import subprocess

try:
    from setuptools import setup
    from setuptools.command.install import install
except ImportError:
    from distutils.core import setup
    from distutils.command.install import install

from distutils.command.build import build
from distutils.command.build_scripts import build_scripts
from distutils.command.install_data import install_data
from distutils.command.sdist import sdist
from distutils import log
from subprocess import Popen, PIPE
#sys.path.append("lib")
#from contrib.debian.installer import DebianInstaller

#
# Build the command line script
#
class BuildScripts(build_scripts):

    BANG = "#!%(env_executable)s%(env_args)s%(py_executable)s\n"
    PACKAGE_BASE = "package_base = %(package_base)s\n%(lib_path)s\n"
    CONFIG = "%(package_config)s\n"

    def run(self):
        """
        Create the proper scripts for the current platform.
        """
        if not self.scripts:
            return

        # The script can only work with package data
        self.data_files = self.distribution.data_files
        if not(self.data_files):
            return

        if self.dry_run:
            return

        # Ensure the destination directory exists
        self.mkpath(self.build_dir)

        # Data useful for building the script
        install = self.distribution.get_command_obj("install")
        if not(install.install_data):
            return

        self._install_lib = os.path.normpath(install.install_lib)
        self._root = install.root
        if self._root:
            self._root = os.path.normpath(self._root)
        self._java_base = os.path.join(install.install_data,
                                          self.data_files[0][0])
        self._use_py_path = install.use_python_path
        self._java_paths = []
        for jpath in ("saxon_path", "xerces_path", "xml_resolver_path"):
            self._java_paths.append((jpath, getattr(install, jpath)))

        # Build the command line scripts
        self.build_script()

    def _strip_root(self, *paths):
        if not(self._root):
            return paths

        newpaths = []
        for path in paths:
            if path.startswith(self._root):
                newpaths.append(path[len(self._root):])
            else:
                newpaths.append(path)
        return newpaths

    def build_script(self):
        # prepare args for the bang path at the top of the script
        ENV_BIN = '/usr/bin/env'
        env_args = ''
        if self._use_py_path:
            env_exec = ''
            py_exec = sys.executable
        elif os.name == 'posix':
            # Some Solaris platforms may not have an 'env' binary.
            # If /usr/bin/env exists, use '#!/usr/bin/env python'
            # otherwise, use '#!' + sys.executable
            env_exec = os.path.isfile(ENV_BIN) and \
                os.access(ENV_BIN, os.X_OK) and ENV_BIN or ''
            py_exec = env_exec and 'python' or sys.executable
        else:
            # shouldn't matter on non-POSIX; we'll just use defaults
            env_exec = ENV_BIN
            py_exec = 'python'

        # Retrieve actual installation paths
        lib_path, java_base = self._strip_root(self._install_lib,
                                               self._java_base)

        # Just help for non standard installation paths
        if lib_path in sys.path:
            lib_path = ""
        else:
            lib_path = "sys.path.append(r\"%s\")" % lib_path

        # Things to adapt when building an egg
        if "/egg" in lib_path:
            lib_path = ""
            package_base = 'os.path.abspath(os.path.join(os.path.dirname('\
                           '__file__), "..", "..", "share", "dblatex"))'
        else:
            package_base = 'r"%s"' % (java_base)

        # Configuration of the paths used by the package
        config_path = ['xslcover_path=package_base']
        for java_path, value in self._java_paths:
            if value: config_path.append('%s="%s"' % (java_path, value))

        package_config = "config.set_config("
        parsep = ",\n" + len(package_config) * " "
        package_config += "%s)" % parsep.join(config_path)

        script_args = { 'env_executable': env_exec,
                        'env_args': env_exec and (' %s' % env_args) or '',
                        'py_executable': py_exec,
                        'lib_path': lib_path,
                        'package_base': package_base,
                        'package_config': package_config }

        for script in self.scripts:
            self._build_script(script, script_args)

    def _build_script(self, script_name, script_args):

        data = open(script_name).read()

        # Assume that the pattern to replace are blocks of non blank lines
        patterns = [("(^#!.*?\n)", self.BANG),
                    ("(# Package path setup.*?)\n\s*?\n", self.PACKAGE_BASE),
                    ("(# Package configuration.*?)\n\s*?\n", self.CONFIG)]

        # Build a template from the actual package script
        for p, r in patterns:
            m = re.search(p, data, re.M|re.DOTALL)
            if m: data = data.replace(m.group(1), r, 1)

        script = data % script_args
        script_name = os.path.basename(script_name)
        outfile = os.path.join(self.build_dir, script_name)
        fd = os.open(outfile, os.O_WRONLY|os.O_CREAT|os.O_TRUNC, 0755)
        os.write(fd, script)
        os.close(fd)


class Build(build):
    """
    Build the .jar file
    """
    def initialize_options(self):
        build.initialize_options(self)

    def run(self):
        # Do the default tasks
        build.run(self)
        # And build the saxon plugin
        self.build_java()

    def build_java(self):
        # Assumes that make is the GNU make
        cmd = ["make", "-C", "java"]
        subprocess.call(cmd)


def find_programs(utils):
    sys.path.append("lib")
    from contrib.which import which
    util_paths = {}
    missed = []
    for util in utils:
        try:
            path = which.which(util)
            util_paths[util] = path
        except which.WhichError:
            missed.append(util)
    sys.path.remove("lib")
    return (util_paths, missed)


class Sdist(sdist):
    """
    Make the source package, and remove the .pyc files
    """
    def prune_file_list(self):
        sdist.prune_file_list(self)
        self.filelist.exclude_pattern(r'.*.pyc', is_regex=1)


class Install(install):

    user_options = install.user_options + \
                   [('saxon-path=', None, 'Path of saxon.jar'),
                    ('xerces-path=', None, 'Path of xercesImpl.jar'),
                    ('xml-resolver-path=', None, 'Path of xml-resolver.jar'),
                    ('use-python-path', None, 'don\'t use env to locate python')]

    def initialize_options(self):
        install.initialize_options(self)
        self.saxon_path = None
        self.xerces_path = None
        self.xml_resolver_path = None
        self.use_python_path = None
        # Prevents from undefined 'install_layout' attribute
        if not(getattr(self, "install_layout", None)):
            self.install_layout = None

    def run(self):
        # If no build is required, at least build the script
        if self.skip_build:
            self.run_command('build_scripts')

        install.run(self)


class InstallData(install_data):

    def run(self):
        ignore_pattern = os.path.sep + r"(CVS|RCS)" + os.path.sep
        # literal backslash must be doubled in regular expressions
        ignore_pattern = ignore_pattern.replace('\\', r'\\')

        # Walk through sub-dirs, specified in data_files and build the
        # full data files list accordingly
        full_data_files = []
        for install_base, paths in self.data_files:
            base_files = []
            for path in paths:
                if os.path.isdir(path):
                    pref = os.path.dirname(path)
                    for root, dirs, files in os.walk(path):
                        if re.search(ignore_pattern, root + os.sep):
                            continue
                        # Only the last directory is copied, not the full path
                        if not(pref):
                            iroot = root
                        else:
                            iroot = root.split(pref + os.path.sep, 1)[1]
                        idir = os.path.join(install_base, iroot)
                        files = [os.path.join(root, i) for i in files]
                        if files:
                            full_data_files += [(idir, files)]
                else:
                    base_files.append(path)

            if base_files:
                full_data_files += [(install_base, base_files)]

        # Replace synthetic data_files by the full one, and do the actual job
        self.data_files = full_data_files
        rc = install_data.run(self)
        return rc



def get_version():
    return "0.1"
    sys.path.insert(0, "python")
    #from dbtexmf.dblatex import dblatex
    #d = dblatex.DbLatex(base=os.getcwd())
    sys.path.remove("python")
    #return d.get_version()


if __name__ == "__main__":
    classifiers = [
       "Operating System :: OS Independent",
       "Topic :: Text Processing :: Markup :: XML",
       "License :: OSI Approved :: GNU General Public License (GPL)"
    ]

    description = """
       With XSL Coverage you can trace the calls of your XSL stylesheets
       and compute their coverage. Currently it works only with Saxon with the
       help of Tracer plugin provided by the package.
       """

    htdocs = [os.path.basename(p) for p in 
              glob.glob(os.path.join("python", "xslcover", "htdocs", "*"))]
    scripts = glob.glob(os.path.join("scripts", "*"))

    setup(name="xslcoverage",
        version=get_version(),
        description='XSL Coverage',
        author='Benoit Guillon',
        author_email='marsgui@users.sourceforge.net',
        url='http://dblatex.sf.net',
        license='GPL Version 2 or later',
        long_description=description,
        classifiers=classifiers,
        packages=['xslcover',
                  'xslcover.htdocs',
                  'xslcover.dblatex'],
        package_dir={'xslcover':'python/xslcover'},
        package_data={'xslcover.dblatex': ['xsltcover.conf'],
                      'xslcover.htdocs': htdocs},
        data_files=[('share/java', ['java/xslcover.jar'])],
        scripts=scripts,
        cmdclass={'build': Build,
                  'build_scripts': BuildScripts,
                  'install': Install,
                  'install_data': InstallData,
                  'sdist': Sdist}
        )

