# Kiwi - Static Website Creator

## Overview

Given a source folder, Kiwi finds all the text files within the folder,
converts them to HTML using the Kiwimark system, and outputs the results to a
destination folder. 

If no source folder is specified, the current working folder is used.

If no destination folder exists, it defaults to an HTML folder beneath the
source folder. 

The destination folder will be created if it does not already exist.

## Command-Line Parameters

* kiwi -s source_folder -t target_folder

## Dependencies

* Python 2.7+
