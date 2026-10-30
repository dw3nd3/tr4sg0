# The following code is a heavily modified version of the
# code from https://gist.github.com/eliben/5797351
# provided under public domain by Eli Bendersky
import re
import logging
from enum import Enum

from .util import rle_decompress
from .model import Room, RuleCase, Command
from .plugin import manager as plugin_manager
from . import state


class TokenType(Enum):
    COLOR = "COLOR"
    DIRECTIVE = "DIRECTIVE"
    STRING = "STRING"
    BYTE = "BYTE"
    VARID = "VARID"
    EMPTYTOK = "EMPTYTOK"
    COMMA = "COMMA"
    SEMICOLON = "SEMICOLON"
    COLON = "COLON"
    CHARACTER = "CHARACTER"
    EOF = "EOF"


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
    for callback in plugin_manager.plugin_before_parse_callbacks:
        text = callback(text)
    start_token = "D33-ROOM"
    regexdict = {
        regid: re.compile(regex)
        for regid, regex in [
            (TokenType.COLOR, r"[0-9a-fA-F]{6}"),
            (TokenType.VARID, r"[a-z_][a-z0-9_-][a-z0-9_-]+"),
            (TokenType.EMPTYTOK, r"_"),
            (TokenType.BYTE, r"[0-9a-fA-F]{2}"),
            (TokenType.DIRECTIVE, r"[A-Z]{3}"),
            (TokenType.STRING, r"\[([^]]*)\]"),
            (TokenType.COMMA, r","),
            (TokenType.SEMICOLON, r";"),
            (TokenType.COLON, r":"),
            (TokenType.CHARACTER, r"."),
            (TokenType.EOF, r"D33-END"),
        ]
    }
    lx = Lexer(regexdict, skip_whitespace=True)

    try:
        start = text.index(start_token)
    except ValueError:
        logging.error("No D33-ROOM found")
        return None

    room = state.base_room_generator()
    lx.input(text, start + len(start_token))

    try:
        finish = False
        while not finish:
            directive = lx.token(TokenType.DIRECTIVE, TokenType.EOF)
            match directive.val:
                case "PAL":
                    room.palette = [
                        lx.token(TokenType.COLOR, TokenType.EOF).val,
                        lx.token(TokenType.COLOR, TokenType.EOF).val,
                        lx.token(TokenType.COLOR, TokenType.EOF).val,
                        lx.token(TokenType.COLOR, TokenType.EOF).val,
                    ]
                case "LAY":
                    next_ = lx.token(TokenType.STRING, TokenType.CHARACTER)
                    if next_.type == TokenType.STRING:
                        layout = rle_decompress(next_.val)
                        assert (
                            len(layout) == 16 * 16
                        ), "Layout must have size 256, but found %s" % len(layout)
                        room.layout = layout
                    else:
                        room.layout = next_.val + "".join(
                            lx.token(TokenType.CHARACTER).val
                            for _ in range(16 * 16 - 1)
                        )

                case "SPR":
                    key = lx.token(TokenType.VARID)
                    next_ = lx.token(TokenType.STRING, TokenType.CHARACTER)
                    if next_.type == TokenType.STRING:
                        sprite = rle_decompress(next_.val)
                        assert (
                            len(sprite) == 8 * 8
                        ), "Sprites must have size 64, but %s is %s" % (
                            key.val,
                            len(sprite),
                        )
                        room.sprites[key.val] = sprite
                    else:
                        room.sprites[key.val] = next_.val + "".join(
                            lx.token(TokenType.CHARACTER).val for _ in range(8 * 8 - 1)
                        )

                case "MAP":
                    loc = lx.token(TokenType.BYTE, TokenType.CHARACTER)
                    key = lx.token(TokenType.VARID)
                    value = lx.token(TokenType.STRING)
                    if loc.type == TokenType.BYTE:
                        room.idxmap[int(loc.val, 16)][key.val] = value.val
                    else:
                        if loc.val not in room.charmap:
                            room.charmap[loc.val] = {}
                        room.charmap[loc.val][key.val] = value.val

                case "RUL":
                    key = lx.token(TokenType.VARID)
                    antecedent = [
                        set([lx.token(TokenType.VARID, TokenType.EMPTYTOK).val])
                    ]
                    consequent = []
                    while True:
                        token = lx.token(
                            TokenType.VARID,
                            TokenType.EMPTYTOK,
                            TokenType.COMMA,
                            TokenType.SEMICOLON,
                            TokenType.COLON,
                        )
                        match token.type:
                            case TokenType.VARID | TokenType.EMPTYTOK:
                                antecedent[-1].add(token.val)
                            case TokenType.COMMA:
                                pass
                            case TokenType.SEMICOLON:
                                antecedent.append(
                                    set(
                                        lx.token(
                                            TokenType.VARID, TokenType.EMPTYTOK
                                        ).val
                                    )
                                )
                            case TokenType.COLON:
                                break
                    while True:
                        if re.match(r"[A-Z]", lx.peek_first_char()):
                            break
                        consequent.append(
                            Command(
                                lx.token(TokenType.VARID).val,
                                lx.token(TokenType.STRING).val,
                            )
                        )
                    ruleset = room.rules.get(key.val, [])
                    ruleset.append(RuleCase(antecedent, consequent))
                    room.rules[key.val] = ruleset

                case "D33-END":
                    finish = True

                case _:
                    try_user_directive(directive.val, lx)

        for callback in plugin_manager.plugin_after_parse_callbacks:
            room = callback(room)
        return room

    except LexerError as err:
        logging.error(
            "LexerError at position %s: %s" % (err.pos, text[err.pos : err.pos + 10])
        )
        logging.error("  %s" % err.extra)
        logging.error("  Expected %s" % " or ".join(str(e) for e in err.expected))


def try_user_directive(directive, lx):
    user_directive = plugin_manager.plugin_directives.get(directive)
    if user_directive:
        user_directive(lx)
    else:
        logging.error("Unknown directive %s" % directive)
