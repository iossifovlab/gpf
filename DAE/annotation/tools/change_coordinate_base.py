import sys
import argparse
from utilities import *

def get_argument_parser():
    desc = """Program to change the variant coordinates from 0-based to 1-based and vice-versa."""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("-H", help="no header in the input file", default=False, dest="no_header", action="store_true")
    parser.add_argument("-p", "--position", help="label of the column containing the variant's position", required=True, action="store")
    parser.add_argument("-o", "--to-one-base", help="convert to 1-based (default is 0-based)", action="store_true") 
    parser.add_argument("-l", "--label", help="label of the column that will contain the new position", action="store_const", const="new-pos")

    return parser

class CoordinateBaseAnnotator(AnnotatorBase):
    def __init__(self, opts, header=None):
        super(CoordinateBaseAnnotator, self).__init__(opts, header)
        
        if(opts.label == None):
            opts.label = "new-pos"
        opts.label = [opts.label]

        self._new_columns = ["new_pos"]
        self.column_id = assign_values(opts.position, header)

        if self.header:
            self.header += opts.label

        self.base_modifier = -1
        if opts.to_one_base:
            self.base_modifier = 1

    @property
    def new_columns(self):
        return self._new_columns

    def line_annotations(self, line, new_columns):
        pos = int(line[self.column_id-1])
        pos+=self.base_modifier
        return [str(pos)] 

if(__name__ == "__main__"):
    main(get_argument_parser(), CoordinateBaseAnnotator)
