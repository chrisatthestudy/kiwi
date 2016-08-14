#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Kiwi

Simple static web-site generator

Usage:
    kiwi [SOURCE] [--target TARGET] [--template TEMPLATE] [--sortbyfile|--sortbytitle] [--savefile CONFIG] [-vc]
    kiwi --version
                    
Options:                      
    -h --help                   
    --version                   
    -t TARGET --target=TARGET
    -m TEMPLATE --template=TEMPLATE
    -v --verbose                
    -c --contents               
    --sortbyfile                
    --sortbytitle               
    -f CONFIG --savefile=CONFIG

Kiwi takes a directory of text files and exports them to another directory as
web-pages, using KiwiMarkup to convert the text markup into HTML elements.

Alternatively it takes a single file and converts it to an HTML file.

If SOURCE is a single file with a .kiwi extension it is assumed to be a
configuration file, and the details are read. Any other command-line details
will be ignored.

If SOURCE is a directory, all the .txt and .md files in the directory are
processed.  If it is not a directory, it is assumed to be a complete file spec
(optionally including wild cards) and the files it identifies are processed.

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

If the --sortbyfile argument is used, the pages are sorted into order by
filename.

If the --sortbytitle argument is used, the pages are sorted into order
on the basis of the contents of their first non-blank line.

These sort options only have any real effect if the -c (contents) option
is specified, in which case they control the order of the entries in the
index.html page, or if a @@PAGE-NAV element is included in the template
or the files, in which case they control the order that the pages are
navigated through.

The --version option displays the version number and exits.

The --help option displays the help and exits.

Post-Processing

The final output is post-processed before it is written to file, and will
replace meta-data entries found in either the template or the source:

@@TITLE - replaced with the directory name
@@DATE  - replaced with the current date
@@PAGE-NAV - replaced with 'back' and 'next' links between the pages

In addition, user-defined meta-data tags can be included in either the
template or the source files. There should be a declaration of the tag
which specifies the tag name and the replacement text. Any occurrence of
the tag name will be replace with the given text. The replacement text
must be enclosed in double-quotes.

E.g.:

@@CSS:"style.css"

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

"""

# Standard library imports
import os
import glob
import re
import datetime
import json

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
    <header>
      <h1>@@TITLE</h1>
    </header>

    <div id="page">

@@PAGE-NAV

          <article>
@@CONTENTS
          </article>

    </div> <!-- Page -->
  </body>
</html>
"""

class KiwiPage():
    """
    Class to hold details of individual pages, including their source
    and target filenames, and links for page navigation.
    """
    source_file = ""
    target_file = ""
    link = ""
    title = ""

class KiwiPageList():
    """
    Class to hold the list of KiwiPage instances used for building the
    final output files.
    """
    files = []
    target_path = ""

    def add(self, source_file):
        """
        Adds the specified file to the list, retrieving its title,
        and updating links between this file and any adjacent files
        in the list.

        The source_file argument is assumed to contain the full path
        for the file.

        The target_path attribute of this class must be set before
        calling this function.
        """
        page = KiwiPage()
        page.source_file = source_file
        page.target_file = self.target_filename(source_file)

        f = open(source_file)
        title = ""
        for line in f:
            if line.strip() is not "":
                page.title = line.strip()
                page.link  = os.path.basename(page.target_file)
                break
        f.close()
        
        self.files.append(page)
    
    def target_filename(self, source_file):
        # Extract the filename from the complete source path
        path, filename = os.path.split(source_file)
        
        # Remove the extension from the filename
        filename, ext = os.path.splitext(filename)

        # Construct the full target path
        return os.path.join(self.target_path, filename + ".html")

    def sort_by_title(self):
        """
        Sorts the pages by their title.
        """
        self.files = sorted(self.files, key = lambda entry: entry.title)

    def sort_by_file(self):
        """
        Sorts the pages by their title.
        """
        self.files = sorted(self.files, key = lambda entry: entry.source_file)

    def adjacent_files(self, source_file):
        """
        Returns (as a tuple) the KiwiPage instances for the file
        immediately before and immediately after the given file.
        This will always return a tuple of two elements, but one
        or both of them can be nil.
        """
        preceding = None
        following = None
        files = [idx for idx, entry in enumerate(self.files) if entry.source_file == source_file]
        if len(files) > 0:
            pos = files[0]
            if pos > 0:
                preceding = self.files[pos - 1]
            if pos + 1 < len(self.files):
                following = self.files[pos + 1]
        return (preceding, following)
    
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
        self.open_kiwi_file()
        self.verbose = self.params["--verbose"]
        self.pages = KiwiPageList()
        
        self.prepare_template()
        if self.prepare_source_path():
            if self.prepare_target_path():
                self.process_files()

        # If requested, save the config file into the source path
        if self.params["--savefile"]:
            f = open(os.path.join(self.source_path, self.params["--savefile"][0] + ".kiwi"), "w")
            self.params["--savefile"] = None
            f.write(json.dumps(self.params, indent=4, separators=(',', ':')))
            f.close()
                
        return True

    def process_files(self):
        """
        Main processing routine.
        """
        # Sort the pages.
        if self.params["--sortbytitle"]:
            self.pages.sort_by_title()
        elif self.params["--sortbyfile"]:
            self.pages.sort_by_file()    

        if self.params["--contents"]:
            self.create_index()
            
        for page in self.pages.files:
            if self.verbose:
                print page.source_file
            self.load_file(page.source_file)
            self.preprocess_file()
            self.apply_markup()
            self.apply_template()
            self.postprocess_file(page.source_file)
            self.write_page(page.source_file)

    def to_utf8(self, input):
        """
        Function to convert json input into utf-8 (json.load returns Unicode).
        Without this, although self.params loads correctly, when the pages
        are written (in self.write_page) they will sometimes error, for no
        obvious reason.
        
        See stackoverflow.com/questions/956867/how-to-get-string-objects-instead-of-unicode-ones-from-json-in-python
        """
        if isinstance(input, dict):
            return {self.to_utf8(key):self.to_utf8(value) for key,value in input.iteritems()}
        elif isinstance(input, list):
            return [self.to_utf8(element) for element in input]
        elif isinstance(input, unicode):
            return input.encode('utf-8')
        else:
            return input

    def open_kiwi_file(self):
        """
        Checks to see if the command-line arguments specify a .kiwi file
        and if so, opens it and replaces the current params array with
        the contents of the file.
        """
        kiwi_file = self.params["SOURCE"]
        if (kiwi_file is not None) and os.path.exists(kiwi_file):
            filename, ext = os.path.splitext(kiwi_file)
            if ext == ".kiwi":
                f = open(kiwi_file)
                self.params = json.loads(f.read())
                f.close()
                self.params = self.to_utf8(self.params)
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
        
        if os.path.isdir(self.source_path):
            source_files = glob.glob(os.path.join(self.source_path, "*.txt"))
            source_files.extend(glob.glob(os.path.join(self.source_path, "*.md")))
        else:
            filename, ext = os.path.splitext(self.title)
            self.title = filename.title()
            source_files = glob.glob(self.source_path)
            
        for filespec in source_files:
            self.pages.add(filespec)
        
        return (len(self.pages.files) > 0)

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
        self.pages.target_path = self.target_path
        return True

    def load_file(self, source_file):
        f = open(source_file)
        self.input = f.readlines()
        f.close()

    def create_index(self):
        """
        Creates an index.html file containing a list of links to all the
        other files. This also builds the list of files that will be used
        for any page-navigation tags.
        """
        self.input = []

        # Create a UL list, adding a LI tag with a link to the file for each
        # item in the list of pages.
        self.input.append("<h2>Contents</h2>")
        self.input.append("<ul>")
        for page in self.pages.files:
            self.input.append("<li><a href='%s'>%s</a></li>" % (page.link, page.title))
        self.input.append("</ul>")

        self.apply_template()
        self.postprocess_file(os.path.join(self.source_path, "index.txt"))
        self.write_page(os.path.join(self.target_path, "index.html"))
        
    def preprocess_file(self):
        """
        Extracts any meta-data from the current file. This will then be
        used to post-process the final output.
        """
        for line in self.input:
            pass

    def postprocess_file(self, source_file):
        """
        Applies any meta-data elements to the current file.

        TODO: This function is messy and unclear, and needs redesigning.
        """
        # Search for user-defined tag declarations
        user_tags = []
        system_tags = ["@@PAGE-NAV", "@@DATE"]
        
        # RegEx to split the tag into three parts. Only the first and third
        # are used, and are the tag name and replacement text respectively
        # (except for @@DATE tags, where the third part is the date format
        # string).
        pattern = re.compile('(@@[a-zA-Z0-9_-]+)(:("[^"]*"))?', re.IGNORECASE)

        for i in range(0, len(self.output)):
            match = re.search(pattern, self.output[i])
            if match:
                tag = match.group(1)
                replacement = ""
                
                if tag == "@@PAGE-NAV":
                    navigation = ""
                    element = "<a class='page-nav page-%s' href='%s'>%s</a>"
                    
                    adjacent_files = self.pages.adjacent_files(source_file)
                    
                    if adjacent_files[0] is not None:
                        navigation = navigation + element % ("back", adjacent_files[0].link, "< Back&nbsp;")
                        
                    if adjacent_files[1] is not None:
                        navigation = navigation + element % ("next", adjacent_files[1].link, "&nbsp;Next >")
                            
                    replacement = "<div class='page-nav'>%s</div>" % navigation

                elif tag == "@@DATE":
                    if match.group(3):
                        # We've been given a date format. Strip the double-quotes
                        date_format = re.sub('"', '', match.group(3))
                    else:
                        # There's no date format, so use the default
                        date_format = "%d %B %Y"
                    replacement = datetime.datetime.now().strftime(date_format)
                    
                elif match.group(3):
                    # Strip off the double-quotes
                    replacement = re.sub('"', '', match.group(3))

                    # Handle system-defined tags
                    if tag == "@@TITLE":
                        if replacement == "":
                            replacement = self.title

                # Store the tag name and the replacement as a tuple
                if replacement is not "":
                    user_tags.append((tag, replacement))

                    # Remove the tag declaration
                    if tag in system_tags:
                        self.output[i] = re.sub(pattern, tag, self.output[i])                    
                    else:
                        self.output[i] = re.sub(pattern, "", self.output[i])

        found_title = False
        for i in range(0, len(self.output)):
            # Find meta-data tag declarations, in the format:
            #
            #    <TAG>:<REPLACEMENT_CONTENTS>
            #
            # Remove the declaration tag, and replace all other occurrences
            # of the tag with the replacement contents.
            for match in user_tags:
                target  = match[0]
                replace = match[1].strip()
                if (target == "@@TITLE"):
                    found_title = True
                if re.search(target, self.output[i]):
                    # Replace any occurrences of the tag
                    self.output[i] = re.sub(target, replace, self.output[i])
            
            if not found_title:
                if re.search("@@TITLE", self.output[i]):
                    # Replace any occurrences of the tag
                    self.output[i] = re.sub("@@TITLE", self.title, self.output[i])
                
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

        """
        ### BUG: Temporary fix for a problem where occasional files would
                 fail to be written, claiming to find an invalid character.
                 Writing such files line-by-line instead seems to fix the
                 problem. Needs further investigation!
                 
                 UPDATE: This appears to be triggered by loading a .kiwi
                 file, which json.loads() imports as Unicode. I don't know
                 why this causes writing the pages to occasionally fail,
                 but I've currently fixed it by converting the imported
                 Unicode to utf-8 (see self.to_utf8).
        """
        f = open(target_file, 'w')

        output = "\n".join(self.output)
        try:
            f.write(output)
        except Exception, e:
            for line in self.output:
                f.write(line + "\n")
                
        f.close()

    def target_filename(self, source_file):
        # Extract the filename from the complete source path
        path, filename = os.path.split(source_file)
        
        # Remove the extension from the filename
        filename, ext = os.path.splitext(filename)

        # Construct the full target path
        return os.path.join(self.target_path, filename + ".html")
        
if (__name__ == "__main__"):
    params = docopt(__doc__, version='Kiwi, version 0.0.32')
    # print params
    
    api = Kiwi()
    api.execute(params)
