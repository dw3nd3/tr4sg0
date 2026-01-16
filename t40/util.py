def rle_decompress(string):
    output = ""
    num = ""
    for char in string:
        if char.isdigit():
            num += char
        else:
            output += char * int(num)
            num = ""
    return output

def rle_compress(string):
    output = ""
    num = 1
    idx = 1
    while idx < len(string):
        if string[idx] == string[idx - 1]:
            num += 1
        else:
            output += str(num) + string[idx-1]
            num = 1
        idx += 1
    output += str(num) + string[idx-1]
    return output

def pos2idx(row, col):
    return row * 16 + col

def idx2pos(idx):
    return idx // 16, idx % 16

def is_valid_pos(row, col):
    return 0 <= row < 16 and 0 <= col < 16

def nc(val1, val2):
    if val1: return val1
    return val2