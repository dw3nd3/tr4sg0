from dataclasses import dataclass

from .util import pos2idx, idx2pos, is_valid_pos, rle_decompress, nc

@dataclass
class Command:
    varid: str
    arg: str

@dataclass
class RuleCase:
    antecedents: list[set[str]]
    consequent: list[Command]

@dataclass
class Room:
    layout: str
    palette: tuple[str, str, str, str]
    sprites: dict[str, str]
    rules: dict[str, list[RuleCase]]
    charmap: dict[str, dict[str, str]]
    idxmap: list[dict[str, str]]

    def __post_init__(self):
        if self.layout:
            self.start = 0
        else:
            self.start = idx2pos(self.layout.index("@")) if "@" in self.layout else 0
            self.layout = self.layout.replace("@", ".")
    
    def _get_tile_value(self, row, col, key):
        if not is_valid_pos(row, col):
            return
        idx = pos2idx(row, col)
        value = self.idxmap[idx].get(key)
        if value is None:
            char = self.layout[idx]
            value = self.charmap[char][key]
        return value
    
    def is_solid(self, row, col):
        return self._get_tile_value(row, col, "solid") == "1"

    def sprite(self, row, col):
        return self._get_tile_value(row, col, "sprite")

    def interact(self, row, col, inventory):
        ruleid = _get_tile_value(pos, "rule")
        if ruleid is not None:
            ruleset = self.rules[ruleid]

            for rule_case in ruleset:
                if any(a.issubset(inventory) for a in rule_case.antecedents):
                    return rule_case.consequent
    
    def color(self, char):
        return self.palette[ord(char) - ord('a')]

    @classmethod
    def default(cls):
        return cls(
            layout="@" + "." * 264,
            palette=("000000", "ffffff", "ffff00", "0000ff"),
            sprites={
                "tile": rle_decompress("64b"),
                "wall": rle_decompress("9a6b2a1b4a1b2a1b4a1b2a1b4a1b2a1b4a1b"),
                "sign": rle_decompress("9a6d2a1d4c1d2a6d9a3b2a6b2a6b2a3b"),
                "chest": rle_decompress("1b6a1b1a6d2a6d4a2c4a2d2c2d2a6d2a6d1a1b6a1b"),
                "door": "aaaaaaaaacdcdcdaadcdcdcaacdcdcdaadcdcdcaacdcdcdaabbbbbbabbbbbbbb",

            },
            rules={},
            charmap={
                ".": {"sprite": "tile"},
                "#": {"sprite": "wall", "wall": "1"},
                "T": {"sprite": "sign", "wall": "1"},
                "O": {"sprite": "chest", "wall": "1"},
                "E": {"sprite": "door", "wall": "1"},
            },
            idxmap=[{} for _ in range(16 * 16)]
        )
