# workon Overview

The workon tool enables quick, repeatable context switching between collections of tools. The theory is that when moving between different projects or workflows, efficiency can be gained by quickly re-establishing the associated tools while removing unrelated tools.

# How it works

The workon tool maintains definition of each context. The description is contained in a JSON file that defines the applications that need to run when re-establishing a context. An example context definition is shown below.


    {
        "Kanban": {
            "command": "/usr/bin/firefox",
            "args": "/home/user/.context/context.kanban/index.html"
            "env": {
                "KANBAN_VAR": "variable contents"
            }
        },
        "Overleaf": {
            "command": "/opt/google/chrome/chrome",
            "args": "http://overleaf/"
        }
    }

This example represents a context with 2 tools: a Kanban board for tracking issues through a linear workflow, and an overleaf instance accessed through a web browser. workon assumes that nearly every context will need to manage and track issues. Therefore, every new context created by workon is given its own Kanban instance.

The user can add additional tools that need to be run for a context by manually editing the json file for that context. The json files for the contexts are stored in the ".context" subdirectory of the user's home directory.

# Configuration file

A configuration file named ".workon.cfg" is created in the user's home directory after the first time the tool runs. The configuration file holds user configurable variables.

# Functions

There are predefined tools called "functions" included with workon. The function names can be found at the bottom of the verbose listing output:

    workon -lv

The functions defintions are in the function_dir subdirectory in the context directory. Users can add their own custom functions by adding a function template to the function_dir. The templates use the same JSON format as the context files and can optionally include the following placeholder values:

    <name>:         Will be replaced with the name of the context
    <context_dir>:  Will be replaced with the context directory path

# Usage

    workon [-h] [-l] [-v] [-c] [-a] [-s] [-n] [-e] [-f FUNCTION] [--archive] [--restore]
                  [--list-archive] [--time-spent] [--date-begin DATE_BEGIN] [--date-end DATE_END]
                  [--add-time ADDITIONAL_TIME]
                  [context]
    
    Establish/switch project contexts.
    
    positional arguments:
      context               Name of the context to create/open/close
    
    optional arguments:
      -h, --help            show this help message and exit
    
    List available contexts/pre-defined functions:
      -l, --list            List the available contexts
      -v, --verbose         Verbose output for listing (shows pre-defined functions)
    
    Change/show running context:
      -c, --close           Close a running context
      -a, --add             Add to the current running context
      -s, --show            Show the current running context
    
    Edit context definition:
      -n, --new             Create a new context
      -e, --edit            Edit a context definition
      -f FUNCTION, --function FUNCTION
                            Add/list pre-defined function to a context definition
    
    Archive:
      --archive             Archive a context. Can be restored later.
      --restore             Restore a context from the archive.
      --list-archive        List the contexts in the archive.
    
    Time Tracking:
      --time-spent          Display the amount of time spent in a context.
      --date-begin DATE_BEGIN
                            Beginning date for time spent. Format: YYYYMMDD
      --date-end DATE_END   End date for time spent. Format: YYYYMMDD
      --add-time ADDITIONAL_TIME
                            Elapsed time to add. Format: HH:MM:SS

# Installation

To install, run the following command from the root directory:

    sudo python setup.py install

# Bash Complete

To enable bash completion for context names, add the following to the user's .bashrc:


    function _workon_complete_()
    {
        local cmd="${1##*/}"
        local word=${COMP_WORDS[COMP_CWORD]}
        local line=${COMP_LINE}
        local workon_sessions=$(python3 ~/bin/workon.py -l)
    
        COMPREPLY=($(compgen -W "$workon_sessions" -- "$word"))
    }
    complete -F _workon_complete_ workon

