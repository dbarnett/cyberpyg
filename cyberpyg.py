import glob
import logging
from optparse import OptionParser
import os
import sys

class SyntaxInstance(object):
    __file__ = None

    @classmethod
    def from_special_string(cls, syntax_string):
        spans = []
        syntax_string_lines = syntax_string.split('\n')
        it = iter(syntax_string_lines)
        for line in it:
            if line == '---':
                break
            start, end, tokencode = line.split(' ')
            start_col, start_row = map(int, start.split(','))
            end_col, end_row = map(int, end.split(','))
            spans.append(((start_col, start_row),
                        (end_col, end_row),
                        tokencode))
        syntax_text = '\n'.join(list(it))
        return cls(syntax_text, spans)

    @classmethod
    def from_file(cls, fname):
        with open(fname, 'r') as f:
            syntax_inst = cls.from_special_string(f.read())
        syntax_inst.__file__ = os.path.abspath(fname)
        return syntax_inst

    def __init__(self, text, spans):
        self.text = text
        self.spans = spans

def main(argv=None):
    if argv is None:
        argv = sys.argv
    opt_parser = OptionParser(usage="%prog [options] command")
    opt_parser.add_option('-s', '--format-specs', dest='format_specs_dir',
            default="format_specs", help="path to syntax example sets")
    options, args = opt_parser.parse_args(argv[1:])
    command = args[0]

    formats = {}
    syntax_fnames = glob.glob(os.path.join(options.format_specs_dir, '*', '*.syntax'))
    if len(syntax_fnames) == 0:
        logging.warning("No syntax files found at '%s'"%(options.format_specs_dir,))
    for fname in syntax_fnames:
        logging.info("Processing syntax file '%s'"%(fname,))
        path, basename = os.path.split(fname)
        _, syntax_name = os.path.split(path)
        format_spec = formats.setdefault(syntax_name, [])
        format_spec.append(SyntaxInstance.from_file(fname))

    if command == 'dump':
        full_path = args[1]
        path, fname = os.path.split(full_path)
        _, syntax_name = os.path.split(path)
        format_syntaxes = formats[syntax_name]
        syntaxes = [s for s in format_syntaxes if s.__file__ == os.path.abspath(full_path)]
        for syntax in syntaxes:
            print syntax.text.rstrip('\n')

    return 0

if __name__ == '__main__':
    sys.exit(main())
