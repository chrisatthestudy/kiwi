# Kiwi - Static Website Creator

## Overview

Kiwi takes a directory of text files and exports them to another directory as
web-pages, using KiwiMarkup to convert the text markup into HTML elements.

Alternatively it takes a single file and converts it to an HTML file.

## Command-line Parameters

    kiwi [SOURCE] [-t TARGET] [-m TEMPLATE] [-v]
    kiwi --version
    kiwi [-h | --help]

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

### Post-Processing

The final output is post-processed before it is written to file, and will
replace meta-date entries found in either the template or the source:

* @@TITLE - replaced with the directory name
* @@DATE  - replaced with the current date

In addition, user-defined tags can be included in either the template or
the source files. There should be a declaration of the tag which specifies
the tag name and the replacement text. Any occurrence of the tag name will
be replace with the given text.

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

## Dependencies

* Python 2.7+

