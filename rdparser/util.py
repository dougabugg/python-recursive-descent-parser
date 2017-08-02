def pos_to_line_col(source, pos):
    offset = 0
    line = 0
    for line in source.splitlines():
        _offset = offset
        line += 1
        offset += len(line) + 1
        if offset > pos:
            return line, pos - _offset + 1
