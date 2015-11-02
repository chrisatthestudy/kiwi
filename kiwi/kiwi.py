#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Kiwi

Simple static web-site generator

Kiwi takes a directory of text files and exports them to another directory as
web-pages, using KiwiMarkup to convert the text markup into HTML elements.

Alternatively it takes a single file and converts it to an HTML file.

If SOURCE is a directory, all the .txt files in the directory are processed.
If it is not a directory, it is assumed to be a text file and is processed.

If SOURCE is not specified, any .txt files in the current working directory
are processed.

If TARGET is a directory, the HTML files are output to this directory.

If TARGET is not specified, and SOURCE is a directory, an 'html' directory
will be created (if it does not already exist) under the SOURCE directory,
and the HTML files will be output to this directory.

If TARGET is not specified, and SOURCE is a file, an HTML file with the same
base name as the SOURCE file (but with an .html extension) will be output in
the same directory as the SOURCE file.

If the -m option is included, it should reference a file which contains the
HTML template that will be wrapped around the content generated from the 
SOURCE file or files. A @@CONTENTS marker must be included in this template,
to indicate the point at which the converted output will be inserted.

If no -m option is specified, Kiwi will use a simple default template.

If the -v (verbose) option is specified, each file will be listed as it is
processed.

If the -c (contents) option is specified, Kiwi will create an index.html
file with a 'contents' list of links to all the other files.

The --version option displays the version number and exits.

The --help option displays the help and exits.

Post-Processing

The final output is post-processed before it is written to file, and will
replace meta-data entries found in either the template or the source:

    @@TITLE - replaced with the directory name
    @@DATE  - replaced with the current date

In addition, user-defined meta-data tags can be included in either the
template or the source files. There should be a declaration of the tag
which specifies the tag name and the replacement text. Any occurrence of
the tag name will be replace with the given text.

E.g.:

    @@CSS:style.css

would declare a CSS tag with "style.css" as the replacement text. This tag
declaration is deleted after it has been read.

The contents will then replace any other occurrence of the tag name.

E.g.:

    <link rel=stylesheet href="@@CSS">

would become:

    <link rel=stylesheet href="style.css">

The above example allows pages to specify the stylesheet individually. Note
that the position of the tag declaration in the file is irrelevant -- tag
references can appear earlier than the declaration, and they will still be
replaced correctly.

Usage:
  kiwi [SOURCE] [-t TARGET] [-m TEMPLATE] [-vc]
  kiwi --version
Arguments:
  SOURCE                     source folder
Options:
  -h --help                  show this help message and exit
  --version                  show version and exit
  -t TARGET --target=TARGET  target folder, defaults to SOURCE/html
  -m --template=TEMPLATE     html file to use as template
  -v --verbose               displays processing details
  -c --contents              generates a contents (index.html) page
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
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>@@TITLE</title>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/css/bootstrap.min.css">
    <style>
      html {  padding: 10px 10px 200px;  }
      body { margin: 0 auto;  max-width: 768px;  line-height: 1.6em; padding: 0.5em; }
      p { font-size: 16px; }
      th, td {  border: #ccc 1px solid; padding: 0.2em;  }
    </style>
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
            self.source_path = os.path.abspath(self.params["SOURCE"])
        else:
            self.source_path = os.getcwd()
        self.title = os.path.split(self.source_path)[1].title()
        if os.path.exists(self.source_path):
            if os.path.isdir(self.source_path):
                self.source_files = glob.glob(os.path.join(self.source_path, "*.txt"))
            else:
                filename, ext = os.path.splitext(self.title)
                self.title = filename.title()
                self.source_files = [self.source_path]
            return (len(self.source_files) > 0)
        else:
            print "Path not found: %s" % self.source_path
            return False

    def prepare_target_path(self):
        """
        Prepares the path that the final HTML files will be written to. Uses
        the target path supplied in the command-line, if any, otherwise
        defaults to an "html" directory under the source path, unless the
        source was a single file, in which case it defaults to the directory
        of the source file. The directory is created if it does not exist.
        """
        if self.params["--target"]:
            self.target_path = os.path.abspath(self.params["--target"])
        else:
            if os.path.isdir(self.source_path):
                self.target_path = os.path.join(self.source_path, "html")
            else:
                self.target_path = os.path.dirname(os.path.abspath(self.source_path))
        if not os.path.exists(self.target_path):
            os.makedirs(self.target_path)
        return True

    def load_file(self, source_file):
        f = open(source_file)
        self.input = f.readlines()
        f.close()

    def create_index(self):
        """
        Creates an index.html file containing a list of links to all the
        other files.
        """
        # Build a list of all the pages.
        page_list = []
        self.input = []

        # For each page, extract the first non-blank line and take this as the title
        # for the page.
        for source_file in self.source_files:
            f = open(source_file)
            title = ""
            for line in f:
                if line.strip() is not "":
                    title = line.strip()
                    link_file = os.path.basename(self.target_filename(source_file))
                    page_list.append((link_file, title))
                    break
            f.close()

        # Sort the list by title.
        sorted_list = sorted(page_list, key = lambda entry: entry[1])

        # Create a UL list, adding a LI tag with a link to the file for each
        # item in the list of pages.
        self.input.append("<h2>Contents</h2>")
        self.input.append("<ul>")
        for item in sorted_list:
            self.input.append("<li><a href='%s'>%s</a></li>" % item)
        self.input.append("</ul>")

        self.apply_template()
        self.postprocess_file()
        self.write_page(os.path.join(self.target_path, "index.html"))
        
    def process_files(self):
        """
        Main processing routine.
        """
        if self.params["--contents"]:
            self.create_index()
            
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
        # Search for user-defined tag declarations
        user_tags = []
        pattern = re.compile('(@@[a-zA-Z0-9_-]+):(.*)', re.IGNORECASE)
        for i in range(0, len(self.output)):
            match = re.search(pattern, self.output[i])
            if match:
                # Store the tag name and the replacement as a tuple
                user_tags.append((match.group(1), match.group(2)))
                # Remove the tag declaration
                self.output[i] = re.sub(pattern, "", self.output[i])
        
        for i in range(0, len(self.output)):
            # Handle the @@TITLE tag
            if re.search("@@TITLE", self.output[i]):
                self.output[i] = re.sub("@@TITLE", self.title, self.output[i])

            # Handle the @@DATE tag
            if re.search("@@DATE", self.output[i]):
                self.output[i] = re.sub("@@DATE", datetime.datetime.now().strftime("%d %B %Y"), self.output[i])

            # Find user-defined meta-data tag declarations, in the format:
            #
            #    <TAG>:<REPLACEMENT_CONTENTS>
            #
            # Remove the declaration tag, and replace all other occurrences
            # of the tag with the replacement contents.
            for match in user_tags:
                target  = match[0]
                replace = match[1].strip()
                if re.search(target, self.output[i]):
                    # Replace any occurrences of the tag
                    self.output[i] = re.sub(target, replace, self.output[i])
            
                      
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
        target_file = self.target_filename(source_file)
        
        f = open(target_file, 'w')
        f.write("\n".join(self.output))
        f.close()

    def target_filename(self, source_file):
        # Extract the filename from the complete source path
        path, filename = os.path.split(source_file)
        
        # Remove the extension from the filename
        filename, ext = os.path.splitext(filename)

        # Construct the full target path
        return os.path.join(self.target_path, filename + ".html")
        
if (__name__ == "__main__"):
    params = docopt(__doc__, version='Kiwi, version 0.0.9')
    # print params
    
    api = Kiwi()
    api.execute(params)
