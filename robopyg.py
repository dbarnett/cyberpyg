import glob
import os
import sys

class SyntaxInstance(object):
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
                        int(tokencode)))
        syntax_text = '\n'.join(list(it))
        return cls(syntax_text, spans)

    def __init__(self, text, spans):
        self.text = text
        self.spans = spans

def main(argv=None):
    if argv is None:
        argv = sys.argv
    formats = {}
    format_specs_dir = argv[1]
    syntax_fnames = glob.glob(os.path.join(format_specs_dir, '*', '*.syntax'))
    for fname in syntax_fnames:
        path, basename = os.path.split(fname)
        _, syntax_name = os.path.split(path)
        with open(fname, 'r') as f:
            format_spec = formats.setdefault(syntax_name, [])
            syntax_inst = SyntaxInstance.from_special_string(f.read())
            format_spec.append(syntax_inst)
    return 0

if __name__ == '__main__':
    sys.exit(main())
