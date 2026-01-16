
# The following code is a heavily modified version of the
# code from https://gist.github.com/eliben/5797351
# provided under public domain by Eli Bendersky
import re
import logging

from .util import rle_decompress
from .model import Room, RuleCase, Command

class Token(object):
    def __init__(self, type, val):
        self.type = type
        self.val = val

    def __repr__(self):
        return "%s(%s)" % (self.type, self.val)

class LexerError(Exception):
    def __init__(self, pos, expected=None, extra=None):
        self.pos = pos
        self.expected = expected
        self.extra = extra


class Lexer(object):
    def __init__(self, regexdict, skip_whitespace=True):
        self.regexdict = regexdict
        self.skip_whitespace = skip_whitespace
        self.re_ws_skip = re.compile(r"\S")
        self.last_token = None

    def _skip_whitespace(self):
        if self.skip_whitespace:
            m = self.re_ws_skip.search(self.buf, self.pos)

            if m:
                self.pos = m.start()
            else:
                return None

    def input(self, buf, pos=0):
        self.buf = buf
        self.pos = pos
        self._skip_whitespace()

    def token(self, *expected):
        if self.peek_first_char() == "<":
            self.pos = self.buf.index(">", self.pos) + 1
        if self.pos >= len(self.buf):
            return None
        else:
            for expected_type in expected:
                m = self.regexdict[expected_type].match(self.buf, self.pos)
                if m:
                    captured = m.group(len(m.groups()))
                    tok = Token(expected_type, captured)
                    self.pos = m.end()
                    self._skip_whitespace()
                    self.last_token = tok
                    return tok

            raise LexerError(self.pos, expected, "Last token: %s" % self.last_token)
    
    def peek_first_char(self):
        if self.pos >= len(self.buf):
            return None
        return self.buf[self.pos]


def parse(text):

    regexdict = {
        regid: re.compile(regex)
        for regid, regex in
        [
            ("COLOR", r"[0-9a-fA-F]{6}"),
            ("VARID", r"[a-z_][a-z0-9_-][a-z0-9_-]+"),
            ("EMPTYTOK", r"_"),
            ("BYTE", r"[0-9a-fA-F]{2}"),
            ("DIRECTIVE", r"[A-Z]{3}"),
            ("STRING", r"\[([^]]*)\]"),
            ("COMMA", r","),
            ("SEMICOLON", r";"),
            ("COLON", r":"),
            ("CHARACTER", r"."),
            ("EOF", r"D33-END"),
        ]
    }
    lx = Lexer(regexdict, skip_whitespace=True)

    try:
        start = text.index("D33-ROOM")
    except ValueError:
        logging.error("No D33-ROOM found")
        return None

    room = Room.default()
    lx.input(text, start+8)

    try:
        finish = False
        while not finish:
            directive = lx.token("DIRECTIVE", "EOF")
            match directive.val:
                case "PAL":
                    room.palette = [
                        lx.token("COLOR", "EOF").val,
                        lx.token("COLOR", "EOF").val,
                        lx.token("COLOR", "EOF").val,
                        lx.token("COLOR", "EOF").val,
                    ]
                case "LAY":
                    next_ = lx.token("STRING", "CHARACTER")
                    if next_.type == "STRING":
                        room.layout = rle_decompress(next_.val)
                    else:
                        room.layout = next_.val + "".join(
                            lx.token("CHARACTER").val for _ in range(16 * 16 - 1)
                        )

                case "SPR":
                    key = lx.token("VARID")
                    next_ = lx.token("STRING", "CHARACTER")
                    if next_.type == "STRING":
                        room.sprites[key.val] = rle_decompress(next_.val)
                    else:
                        room.sprites[key.val] = next_.val + "".join(
                            lx.token("CHARACTER").val for _ in range(8 * 8 - 1)
                        )

                case "MAP":
                    loc = lx.token("BYTE", "CHARACTER")
                    key = lx.token("VARID")
                    value = lx.token("STRING")
                    if loc.type == "BYTE":
                        room.idxmap[int(loc.val, 16)][key.val] = value.val
                    else:
                        room.charmap[loc.val][key.val] = value.val

                case "RUL":
                    antecedent = []
                    consequent = []
                    key = lx.token("VARID")
                    while True:
                        token = lx.token("VARID", "EMPTYTOK", "COMMA", "SEMICOLON", "COLON")
                        match token.type:
                            case "VARID"|"EMPTYTOK": antecedent.append(token.val)
                            case "COMMA": pass
                            case "SEMICOLON": 
                                rule_case.antecedents.append(antecedent)
                                antecedent = []
                            case "COLON": break
                    while True:
                        if re.match(r'[A-Z]', lx.peek_first_char()):
                            break
                        consequent.append(Command(lx.token("VARID").val, lx.token("STRING").val))
                    ruleset = room.rules.get(key.val, [])
                    ruleset.append(RuleCase(antecedent, consequent))
                    room.rules[key.val] = ruleset

                case "D33-END":
                    finish = True

        return room
    
    except LexerError as err:
        logging.error("LexerError at position %s: %s" % (err.pos, text[err.pos:err.pos+10]))
        logging.error("  %s" % err.extra)
        logging.error("  Expected %s" % " or ".join(err.expected))

