import glob
import logging
from optparse import OptionParser
import os
import sys

import colorama

default_color_order = ['RED', 'BLUE', 'CYAN', 'MAGENTA', 'GREEN', 'YELLOW']
default_colors = [getattr(colorama.Fore, c, '') for c in default_color_order]

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
            start, end, tokencode = line.split(None, 2)
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

    def linear_spans(self):
        lin_index = lambda row, col: sum(len(r)+len('\n') for r in self.text.splitlines()[:row-1]) + col - 1
        return ((lin_index(*s), lin_index(*e)+1, tok_t) for (s, e, tok_t) in self.spans)

    def iterspans(self):
        last_end = 0
        # sorts earliest first, shortest first, then alphabetical by token
        for (s, e, tok_t) in sorted(self.linear_spans()):
            if last_end < s:
                yield (last_end, s, None)
            yield (max(last_end, s), e, tok_t)
            last_end = e
        if last_end < len(self.text):
            yield (last_end, len(self.text), None)

    def itertokens(self):
        for (s, e, tok_t) in self.iterspans():
            yield (self.text[s:e], tok_t)

    def text_with_colors(self):
        token_types = sorted(set(tok_t for (s, e, tok_t) in self.spans))
        token_colors = dict(zip(token_types, default_colors))
        for (text, tok_t) in self.itertokens():
            yield (text, token_colors.get(tok_t, ''))

def main(argv=None):
    if argv is None:
        argv = sys.argv
    opt_parser = OptionParser(usage="%prog [options] command")
    opt_parser.add_option('-s', '--format-specs', dest='format_specs_dir',
            default="format_specs", help="path to syntax example sets")
    options, args = opt_parser.parse_args(argv[1:])
    command = (args[0] if len(args) > 0 else None)
    if command is None:
        opt_parser.print_help()
        return 1

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
        first = True
        for syntax in syntaxes:
            if not first:
                sys.stdout.write('\n')
            first = False
            for (text, color) in syntax.text_with_colors():
                sys.stdout.write(color + text + colorama.Style.RESET_ALL)
    if command == 'pygments':
        format_name = args[1]
        syntax_instances = formats[format_name]
        tok_instances = {}
        for s_instance in syntax_instances:
            for tok_text, tok_type in s_instance.itertokens():
                tok_instances.setdefault(tok_type, []).append(tok_text)
        tok_regexes = {}
        for tok_type, tok_texts in tok_instances.items():
            tok_chars = set(c for c in ''.join(tok_texts))
            if any(tok_chars&set(c for c in ''.join(tok2_texts)) for (tok2_type, tok2_texts) in tok_instances.items() if tok2_type != tok_type):
                raise Exception("Not smart enough")
            tok_regex = '['+''.join('\\'+t if t in r'[]\^$.|?*+()' else t for t in tok_chars)+']+'
            if tok_type is not None:
                tok_regexes[tok_type] = tok_regex
        print """from pygments.lexer import RegexLexer
from pygments.token import *

class %(format_name)s_Lexer(RegexLexer):
    tokens = {
        'root': [%(tok_tuples)s
        ]
    }"""%{'format_name': format_name,
        'tok_tuples': '\n            '.join('(%r, Token.%s),'%(tok_regex, tok_type[:1].upper()+tok_type[1:]) for (tok_type, tok_regex) in tok_regexes.items())
    }

    return 0
