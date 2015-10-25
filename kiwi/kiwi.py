#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Kiwi
Simple static web-site generator

Kiwi takes a directory of text files and exports them to another directory as
web-pages, using KiwiMarkup to convert the text markup into HTML elements.

Usage:
  kiwi [SOURCE] [-t TARGET] [-m TEMPLATE] [-v]
  kiwi --version
Arguments:
  SOURCE                     source folder
Options:
  -h --help                  show this help message and exit
  --version                  show version and exit
  -t TARGET --target=TARGET  target folder, defaults to SOURCE/html
  -m --template=TEMPLATE     html file to use as template
  -v --verbose               displays processing details
"""

# Standard library imports
import os
import glob
import re
import datetime

# Third party imports
from docopt import docopt

# Application specific imports
import kiwimark

DEFAULT_PAGE_TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>@@TITLE</title>
    <link rel="stylesheet" href="css/style.css" type="text/css" media="Screen">
  </head>
  <body>
    <div id="page">

          <article>
@@CONTENTS
          </article>

    </div> <!-- Page -->
  </body>
</html>
"""

class Kiwi():

    """
    Main processor class, with Kiwi.execute() as the entry-point.
    """
    def __init__(self):
        self.marker = kiwimark.KiwiMarkup()
        
    def execute(self, params):
        """
        Main entry point.

        params - docopt object containing command-line parameters
        """
        self.params = params
        self.verbose = params["--verbose"]
        self.prepare_template()
        if self.prepare_source_path():
            if self.prepare_target_path():
                self.process_files()
        return True

    def prepare_template(self):
        """
        Prepares the HTML template that the contents of each file will be
        inserted into. If no template file was specified on the command
        line, a simple internal template is used instead.
        """
        self.template = DEFAULT_PAGE_TEMPLATE
        if self.params["--template"] != None:
            template_file = self.params["--template"]
            if os.path.exists(template_file):
                f = open(template_file)
                self.template = f.read()
                f.close
            elif self.verbose:
                print "Template file %s not found, using default instead." % template_file

    def prepare_source_path(self):
        """
        Sets the source path, either from the command-line
        parameters, or using the current path if no path was
        supplied. Ensures that the path exists, and reads a list of text
        files from it.

        Returns False if the path could not be found or if no text files were
        found, otherwise returns True.
        """
        if self.params["SOURCE"]:
            self.source_path = self.params["SOURCE"]
        else:
            self.source_path = os.getcwd()
        self.title = os.path.split(self.source_path)[1].title()
        if os.path.exists(self.source_path):
            self.source_files = glob.glob(os.path.join(self.source_path, "*.txt"))
            return (len(self.source_files) > 0)
        else:
            print "Path not found: %s" % self.source_path
            return False

    def prepare_target_path(self):
        """
        Prepares the path that the final HTML files will be written to. Uses
        the target path supplied in the command-line, if any, otherwise
        defaults to an "html" directory under the source path. The directory
        is created if it does not exist.
        """
        if self.params["--target"]:
            self.target_path = self.params["--target"]
        else:
            self.target_path = os.path.join(self.source_path, "html")
        if not os.path.exists(self.target_path):
            os.makedirs(self.target_path)
        return True

    def load_file(self, source_file):
        f = open(source_file)
        self.input = f.readlines()
        f.close()
        
    def process_files(self):
        """
        Main processing routine.
        """
        for source_file in self.source_files:
            if self.verbose:
                print source_file
            self.load_file(source_file)
            self.preprocess_file()
            self.apply_markup()
            self.apply_template()
            self.postprocess_file()
            self.write_page(source_file)

    def preprocess_file(self):
        """
        Extracts any meta-data from the current file. This will then be
        used to post-process the final output.
        """
        for line in self.input:
            pass

    def postprocess_file(self):
        """
        Applies any meta-data elements to the current file.
        """
        for i in range(0, len(self.output)):
            if re.search("@@TITLE", self.output[i]):
                self.output[i] = re.sub("@@TITLE", self.title, self.output[i])
            if re.search("@@DATE", self.output[i]):
                self.output[i] = re.sub("@@DATE", datetime.datetime.now().strftime("%d %B %Y"), self.output[i])
                      
    def apply_markup(self):
        """
        Uses a KiwiMarkup instance to process the current file and
        convert it into HTML format. The lines to be processed are
        expected to be in self.input, which will be replaced by
        the formatted lines.
        """
        self.marker.execute(self.input, kiwimark.KIWI_MODE_STD)
        self.input = self.marker.output

    def apply_template(self):
        """
        Wraps the converted HTML lines with the supplied template -- it looks
        for a @@CONTENTS marker in the template, and replaces this with the
        processed lines.
        """
        template_lines = [re.sub("\n", "", line) for line in self.template.split("\n")]
        self.output = []
        for line in template_lines:
            if line.strip().upper() == "@@CONTENTS":
                self.output.extend(self.input)
            else:
                self.output.append(line)

    def write_page(self, source_file):
        """
        Writes the final HTML page to the target folder.
        """
        # Extract the filename from the complete source path
        path, filename = os.path.split(source_file)
        
        # Remove the extension from the filename
        filename, ext = os.path.splitext(filename)

        # Construct the full target path
        target_file = os.path.join(self.target_path, filename + ".html")

        f = open(target_file, 'w')

        f.close()
        
if (__name__ == "__main__"):
    params = docopt(__doc__, version='Kiwi, version 0.0.6')
    # print params
    
    api = Kiwi()
    api.execute(params)
