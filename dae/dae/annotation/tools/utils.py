def handle_header(source_header):
    header = []
    for index, col_name in enumerate(source_header):
        col = col_name.strip('#')
        if col in header:
            col = "{}_{}".format(col, index)
        header.append(col)
    return header


class LineMapper(object):

    def __init__(self, source_header):
        self.source_header = handle_header(source_header)

    def map(self, source_line):
        return dict(zip(self.source_header, source_line))
