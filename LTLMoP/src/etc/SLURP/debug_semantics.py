#!/usr/bin/env python
"""
Interface for debugging semantic frame matching.
"""

# Copyright (C) 2011-2013 Constantine Lignos, Ian Perera, and Kenton Lee
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys

from semantics.parsing import (extract_frames_from_parse, create_semantic_structures)
from semantics.tree import Tree
from pipelinehost import PipelineClient
from semantics.semantics_logger import SemanticsLogger


HEADER_WIDTH = 72
MONGODB = False
if MONGODB: semlog = SemanticsLogger()

def process(parse,verbose=True):
    """Show the steps of transformation for a parse."""
    # Original parse
    parse_tree = Tree.parse(parse)
    print_parse(parse_tree, "Parse")

    frames = extract_frames_from_parse(parse, verbose=verbose)
    if verbose:
        print
        for frame in frames:
            print frame.pprint()
            if frame.condition:
                print "Condition:"
                print frame.condition.pprint()
        print

    # Bail if no frames matched
    if not frames:
        if verbose: print "No frames matched."
        return

    # Extract semantic structures
    semantic_structures = create_semantic_structures(frames)
    if semantic_structures:
        if verbose: print semantic_structures
        return semantic_structures
    else:
        if verbose: print "No semantic structures returned."
    


def print_parse(parse, heading):
    """Print a tree in a pretty fashion."""
    # Print a centered header
    header_left = (HEADER_WIDTH - len(heading)) // 2
    header_right = HEADER_WIDTH - header_left
    print "-" * header_left + heading + "-" * header_right
    print parse.pprint(force_multiline=True)
    print


def main():
    """Get input, parse it, and pass it on to process."""
    client = PipelineClient(verbose=True)

    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
        parse = client.parse(text)
        if parse:
            process(parse)            
        else:
            print "Connection to server closed."
    else:
        while True:
            try:
                text = raw_input('> ')
            except (KeyboardInterrupt, EOFError):
                break
            print "text: ",[text]

            semlog_command = False
            if MONGODB: semlog_command = semlog.is_command(text)
            if semlog_command:
                print semlog_command
            else:
                parse = client.parse(text)
                if parse:
                    semantic_structures = process(parse)
                    if semantic_structures and MONGODB:
                        semlog.log_structures(text,semantic_structures)
                    if semantic_structures: 
                        for s in semantic_structures:
                            print "semantic_structure dict: ",s.to_dict()
                else:
                    print "Connection to server closed."
                    break


if __name__ == "__main__":
    main()
