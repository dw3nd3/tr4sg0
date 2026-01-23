from .util import rle_compress

def brackets(string):
    return "[%s]" % string

def shortest(string):
    rle = brackets(rle_compress(string))
    if len(rle) < len(string):
        return rle
    return string

def serialize(room):
    output = "D33-ROOM "
    output += "PAL" + "".join(room.palette)
    output += "LAY" + " " + shortest(room.layout)
    for key, value in room.sprites.items():
        output += "SPR" + key + " " + shortest(value)
    for loc, dictionary in room.charmap.items():
        for key, value in dictionary.items():
            output += "MAP" + loc + key + brackets(value)
    for loc, dictionary in enumerate(room.idxmap):
        for key, value in dictionary.items():
            output += "MAP" + "{:02x}".format(loc) + key + brackets(value)
    for key, value in room.rules.items():
        output += "RUL" + key + " "
        for rule_case in value:
            output += ";".join([",".join(antecedent) for antecedent in rule_case.antecedents])
            output += ":"
            for command in rule_case.consequent:
                output += command.varid + brackets(command.arg)
    output += "D33-END"
    return output        
