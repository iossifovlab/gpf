

def handle_header(source_header):
    header = []
    for index, col_name in enumerate(source_header):
        col = col_name.strip('#')
        if col in header:
            col = "{}_{}".format(col, index)
        header.append(col)
    return header
