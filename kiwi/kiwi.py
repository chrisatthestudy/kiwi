#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Kiwi
Simple static web-site generator

Kiwi takes a folder of text files and exports them in another folder as 
web-pages.

Usage:
  kiwi [SOURCE] [-t TARGET] [-m TEMPLATE] [-v]
  kiwi --version
Arguments:
  SOURCE                     source folder
Options:
  -h --help                  show this help message and exit
  --version                  show version and exit
  -t TARGET --target=TARGET  target folder, defaults to SOURCE/html
  -m --template=TEMPLATE     html file to use as project template
  -v --verbose               displays processing details
"""

# Standard library imports
import os
import glob
import re

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
        self.params = params
        self.verbose = params["--verbose"]
        self.prepare_template()
        if self.prepare_source_path():
            if self.prepare_target_path():
                self.process_files()
        return True

    def prepare_template(self):
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
        if self.params["--target"]:
            self.target_path = self.params["--target"]
        else:
            self.target_path = os.path.join(self.source_path, "html")
        if not os.path.exists(self.target_path):
            os.makedirs(self.target_path)
        return True

    def load_file(self, source_file):
        f = open(source_file)
        self.lines = f.readlines()
        f.close()
        
    def process_files(self):
        for source_file in self.source_files:
            if self.verbose:
                print source_file
            self.load_file(source_file)
            self.preprocess_file()
            self.apply_markup()
            self.apply_template()
            self.write_page(source_file)

    def preprocess_file(self):
        for line in self.lines:
            pass
        
    def apply_markup(self):
        self.marker.execute(self.lines, kiwimark.KIWI_MODE_STD)
        self.output = self.marker.output

    def apply_template(self):
        template_lines = [re.sub("\n", "", line) for line in self.template.split("\n")]
        self.output = []
        for line in template_lines:
            if line.strip().upper() == "@@CONTENTS":
                self.output.extend(self.lines)
            else:
                self.output.extend(line)

    def write_page(self, source_file):
        # Extract the filename from the complete source path
        path, filename = os.path.split(source_file)
        
        # Remove the extension from the filename
        filename, ext = os.path.splitext(filename)

        # Construct the full target path
        target_file = os.path.join(self.target_path, filename + ".html")

        f = open(target_file, 'w')

        for line in self.output:
            line = re.sub("@@TITLE", self.title, line)
            f.write(line)

        f.close()
        
if (__name__ == "__main__"):
    params = docopt(__doc__, version='Kiwi, version 0.0.5')
    # print params
    
    api = Kiwi()
    api.execute(params)
