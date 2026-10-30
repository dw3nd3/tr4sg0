from .util import rle_compress


def brackets(string):
    return "[%s]" % string


def shortest(string):
    rle = brackets(rle_compress(string))
    if len(rle) < len(string):
        return rle
    return string

def expand(room):
    output = "D33-ROOM "
    if room.palette:
        output += "PAL " + " ".join(room.palette) + "\n"
    
    if room.layout:
        lay = room.layout_with_avatar
        output += "LAY\n"
        for i in range(16):
            output += "    " + lay[i*16:(i+1)*16] + "\n"
    
    for key, value in room.sprites.items():
        output += "SPR " + key + "\n"
        for i in range(8):
            output += "    " + value[i*8:(i+1)*8] + "\n"
        
    for loc, dictionary in room.charmap.items():
        for key, value in dictionary.items():
            output += " ".join(["MAP", loc, key+brackets(value)]) + "\n"
    
    for loc, dictionary in enumerate(room.idxmap):
        for key, value in dictionary.items():
            output += " ".join(["MAP", "{:02x}".format(loc), key + brackets(value)]) + "\n"
    
    for key, value in room.rules.items():
        for rule_case in value:
            output += "RUL " + key + " "
            output += "\n    ; ".join(
                [", ".join(antecedent) for antecedent in rule_case.antecedents]
            )
            output += " :"
            for command in rule_case.consequent:
                output += " " + command.varid + brackets(command.arg)
            output += "\n"

    output += "D33-END"
    return output


def minify(room):
    output = "D33-ROOM "
    if room.palette:
        output += "PAL" + "".join(room.palette)
    if room.layout:
        output += "LAY" + shortest(room.layout_with_avatar)
    for key, value in room.sprites.items():
        if short_val := shortest(value).startswith("["):
            output += "SPR" + key + shortest(value)
        else:
            output += "SPR" + key + " " + shortest(value)
    for loc, dictionary in room.charmap.items():
        for key, value in dictionary.items():
            output += "MAP" + loc + key + brackets(value)
    for loc, dictionary in enumerate(room.idxmap):
        for key, value in dictionary.items():
            output += "MAP" + "{:02x}".format(loc) + key + brackets(value)
    for key, value in room.rules.items():
        for rule_case in value:
            output += "RUL" + key + " "
            output += ";".join(
                [",".join(antecedent) for antecedent in rule_case.antecedents]
            )
            output += ":"
            for command in rule_case.consequent:
                output += command.varid + brackets(command.arg)
    output += "D33-END"
    return output
