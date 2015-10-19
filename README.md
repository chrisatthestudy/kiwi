# Kiwi - Static Website Creator

## Overview

Given a source folder, Kiwi finds all the text files within the folder,
converts them to HTML using the Kiwimark system, and outputs the results to a
target folder.

If no source folder is specified, the current working folder is used.

If no target folder exists, it defaults to an HTML folder beneath the
source folder. 

The target folder will be created if it does not already exist.

## Command-Line Parameters

* kiwi [source_folder] [-t target_folder]

## Dependencies

* Python 2.7+
