import glob
import os
import sys

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
            spans = []
            for line in f:
                line = line.rstrip('\n')
                if line == '---':
                    break
                start, end, tokencode = line.split(' ')
                start_col, start_row = map(int, start.split(','))
                end_col, end_row = map(int, end.split(','))
                spans.append(((start_col, start_row),
                            (end_col, end_row),
                            int(tokencode)))
            syntax_text = ''.join(f)
            format_spec.append({'spans': spans, 'text': syntax_text})
    return 0

if __name__ == '__main__':
    sys.exit(main())
