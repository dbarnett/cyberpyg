import glob
import logging
from optparse import OptionParser
import os
import sys

import colorama
from .syntax import SyntaxInstance
from .grokkers import StatefulRegexGrokker

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
                sys.stdout.write(getattr(colorama.Fore, color, '') + text + colorama.Style.RESET_ALL)
    if command == 'pygments':
        format_name = args[1]
        syntax_instances = formats[format_name]
        guesses = StatefulRegexGrokker().grok(syntax_instances)
        if len(guesses) == 0:
            print >>sys.stderr, "Failed to grok syntax"
            return 2
        tok_regexes = guesses[0]
        import pygments.token
        pyg_tokens = {}
        for s, s_rules in tok_regexes.items():
            pyg_tokens.setdefault(s, [])
            for s_rule in s_rules:
                tok_type = s_rule[1]
                pyg_tokens[s].append((s_rule[0], pygments.token.string_to_tokentype(tok_type[:1].upper()+tok_type[1:])) + s_rule[2:])
        print """from pygments.lexer import RegexLexer
from pygments.token import *

class %(format_name)s_Lexer(RegexLexer):
    tokens = %(lexer_dict)r"""%{'format_name': format_name,
        'lexer_dict': pyg_tokens
    }

    return 0
