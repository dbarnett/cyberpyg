"""Code for generating and testing hypotheses about how a syntax works"""

class BaseGrokker(object):
    def grok(self, syntax_instances):
        return []

class DumbRegexGrokker(BaseGrokker):
    def grok(self, syntax_instances):
        tok_instances = {}
        for s_instance in syntax_instances:
            for tok_text, tok_type in s_instance.itertokens():
                tok_instances.setdefault(tok_type, []).append(tok_text)
        tok_regexes = {}
        for tok_type, tok_texts in tok_instances.items():
            tok_chars = set(c for c in ''.join(tok_texts))
            if any(tok_chars&set(c for c in ''.join(tok2_texts)) for (tok2_type, tok2_texts) in tok_instances.items() if tok2_type != tok_type):
                return []
            tok_regex = '['+''.join('\\'+t if t in r'[]\^$.|?*+()' else t for t in tok_chars)+']+'
            if tok_type is not None:
                tok_regexes[tok_type] = tok_regex
        return [tok_regexes]

class StatefulRegexGrokker(BaseGrokker):
    """Represents a model for syntax like pygments.lexers.RegexLexer"""
    pass
