import sys
import pathlib

from dae.genomic_resources.dir_repository import GenomicResourceDirRepo
from dae.genomic_resources.repository import GR_CONF_FILE_NAME


def cli(args=None):
    if not args:
        args = sys.argv[1:]

    dr = "."
    if len(args) > 0:
        dr = args[0]
    dr = pathlib.Path(dr)
    GRR = GenomicResourceDirRepo("", dr)

    for gr in GRR.get_all_resources():
        gr.update_stats()
        gr.update_manifest()

    if not (dr / GR_CONF_FILE_NAME).is_file():
        GRR.save_content_file()


if __name__ == '__main__':
    cli(sys.argv[1:])
