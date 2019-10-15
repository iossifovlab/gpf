import sys
import os
from datetime import datetime

# NOTE: Accepts only time formats as in curl output, e.g.:
# Mon, 14 Oct 2019 10:27:04 GMT

assert len(sys.argv) == 2, sys.argv

timestamp_ref = datetime.utcfromtimestamp(
    int(os.path.getmtime('data-hg19-startup-latest.tar.gz'))
)
timestamp_new = datetime.strptime(sys.argv[1].strip(), '%a, %d %b %Y %H:%M:%S GMT')

sys.exit(int(timestamp_new > timestamp_ref))
