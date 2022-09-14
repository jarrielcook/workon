# workon Overview

The workon tool enables quick, repeatable context switching between collections of tools. The theory is that when moving between different projects or workflows, efficiency can be gained by quickly re-establishing the associated tools while removing unrelated tools.

# How it works

The workon tool maintains definition of each context. The description is contained in a JSON file that defines the applications that need to run when re-establishing a context. An example context definition is shown below.


    {
        "Kanban": {
            "command": "/usr/bin/firefox",
            "args": "/home/user/.context/context.kanban/index.html"
        },
        "Overleaf": {
            "command": "/opt/google/chrome/chrome",
            "args": "http://overleaf/"
        }
    }

This example represents a context with 2 tools: a Kanban board for tracking issues through a linear workflow, and an overleaf instance accessed through a web browser. workon assumes that nearly every context will need to manage and track issues. Therefore, every new context created by workon is given its own Kanban instance.

The user can add additional tools that need to be run for a context by manually editing the json file for that context. The json files for the contexts are stored in the ".context" subdirectory of the user's home directory.

# Usage

workon.py [-h] [-l] [-c] [-a] [-v] [context name]

Establish/switch project context.

positional arguments:
  context        Name of the context to load/create. This argument is required unless -l/--list or -h/--help are specified.

optional arguments:
  -h, --help     show this help message and exit
  -l, --list     List the available contexts
  -v, --verbose  Verbose output
  -c, --create   Create a new context
  -a, --add      Add to the current context

# Installation



