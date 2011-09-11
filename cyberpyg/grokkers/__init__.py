"""Code for generating and testing hypotheses about how a syntax works"""

import re

import pygments.lexer
import pygments.token

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

class CyberTok(object):
    def __init__(self, name):
        self.name = name

SkippedToken = pygments.token.Token.CyberPyg.SkippedToken

class Mu(object):
    pass

class LikelyStatePopError(Exception):
    pass

class StatefulRegexGrokker(BaseGrokker):
    """Represents a model for syntax like pygments.lexers.RegexLexer"""
    @staticmethod
    def _apply_lexer(lexer, text):
        pyg_tokens = {}
        for s, s_rules in lexer.items():
            pyg_tokens.setdefault(s, [])
            for s_rule in s_rules:
                tok_type = s_rule[1]
                pyg_tokens[s].append((s_rule[0], pygments.token.string_to_tokentype(tok_type[:1].upper()+tok_type[1:])) + s_rule[2:])
            pyg_tokens[s].append(('.', SkippedToken))
        class _Lexer(pygments.lexer.RegexLexer):
            tokens = pyg_tokens
        toks = _Lexer().get_tokens(text)
        def fix_pop_errors():
            try:
                while True:
                    yield toks.next()
            except IndexError, e:
                raise LikelyStatePopError()
            except StopIteration, e:
                pass
        return fix_pop_errors()

    @staticmethod
    def _coiterate_tokens(cyber_toks, pygments_toks):
        try:
            cyber_toks = iter(cyber_toks)
            pygments_toks = iter(pygments_toks)
            last_cyber_tok = cyber_toks.next()
            last_pyg_tok = pygments_toks.next()
            while True:
                co_len = min(len(last_cyber_tok[0]), len(last_pyg_tok[1]))
                yield ((last_cyber_tok[1], last_pyg_tok[0]), last_cyber_tok[0][:co_len])
                if len(last_cyber_tok[0]) > co_len:
                    last_cyber_tok = (last_cyber_tok[0][co_len:], last_cyber_tok[1])
                else:
                    last_cyber_tok = cyber_toks.next()
                if len(last_pyg_tok[1]) > co_len:
                    last_pyg_tok = (last_pyg_tok[1][co_len:], last_pyg_tok[0])
                else:
                    last_pyg_tok = pygments_toks.next()
        except StopIteration, e:
            pass

    def grok(self, syntax_instances):
        bfs = [{'root': []}]
        while len(bfs) > 0:
            lexer_guess = bfs.pop(0)
            lexer_inconsistent = False
            for syntax_instance in syntax_instances:
                try:
                    for ((cyb_tok_t, pyg_tok_t), tok_str) in self._coiterate_tokens(syntax_instance.itertokens(), self._apply_lexer(lexer_guess, syntax_instance.text)):
                        if cyb_tok_t is None:
                            if pyg_tok_t is not SkippedToken:       # false positive
                                if ((cyb_tok_t, pyg_tok_t), tok_str) != ((None, pygments.token.Token.Text), '\n'):
                                    lexer_inconsistent = True
                        elif pyg_tok_t is SkippedToken:     # false negative
                            tok_regex = '['+''.join('\\'+t if t in r'[]\^$.|?*+()' else t for t in sorted(set(tok_str)))+']'
                            def _perm_lexer(lexer):
                                for state_to_perm in lexer.keys():
                                    if len(lexer[state_to_perm]) > 0 and lexer[state_to_perm][-1][0] == tok_regex:
                                        continue
                                    i = 1
                                    while 's'+str(i) in lexer.keys():
                                        i += 1
                                    for new_push_state in [Mu, 's'+str(i), '#pop', '#push']:
                                        new_lexer_guess = dict([(s_name, s_rules[:]) for (s_name, s_rules) in lexer.iteritems()])
                                        if new_push_state == Mu:
                                            pattern_to_append = (tok_regex, cyb_tok_t)
                                        else:
                                            if not new_push_state.startswith('#'):
                                                new_lexer_guess[new_push_state] = []
                                            pattern_to_append = (tok_regex, cyb_tok_t, new_push_state)
                                        new_lexer_guess[state_to_perm].append(pattern_to_append)
                                        yield new_lexer_guess
                            bfs.extend(_perm_lexer(lexer_guess))
                            lexer_inconsistent = True
                        elif pygments.token.string_to_tokentype(cyb_tok_t[:1].upper()+cyb_tok_t[1:]) is not pyg_tok_t:
                            lexer_inconsistent = True
                        if lexer_inconsistent:
                            break
                except LikelyStatePopError, e:
                    lexer_inconsistent = True
                if lexer_inconsistent:
                    break
            if not lexer_inconsistent:
                return [lexer_guess]
        return []
