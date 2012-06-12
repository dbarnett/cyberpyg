import os

default_colors = ['RED', 'BLUE', 'CYAN', 'MAGENTA', 'GREEN', 'YELLOW']

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

