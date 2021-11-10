import sys
import pathlib

from dae.genomic_resources.dir_repository import GenomicResourceDirRepo
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.repository_factory import build_genomic_resource_repository


def cli_browse(args=None):
    if not args:
        args = sys.argv[1:]

    grr = build_genomic_resource_repository()
    for gr in grr.get_all_resources():
        print("%20s %20s %-7s %2d %10d %s" %
              (gr.repo.repo_id, gr.get_resource_type(), gr.get_version_str(),
               len(list(gr.get_files())),
                  sum([fs for _, fs, _ in gr.get_files()]), gr.get_id()))


def cli_manage(args=None):
    if not args:
        args = sys.argv[1:]

    if len(args) != 2:
        print("Need two arguments: <command> and <repository directory>")
        return

    cmd, dr = args

    dr = pathlib.Path(dr)
    GRR = GenomicResourceDirRepo("", dr)

    if cmd == "index":
        for gr in GRR.get_all_resources():
            gr.update_stats()
            gr.update_manifest()

        if not (dr / GR_CONF_FILE_NAME).is_file():
            GRR.save_content_file()
    elif cmd == "list":
        for gr in GRR.get_all_resources():

            print("%20s %-7s %2d %10d %s" %
                  (gr.get_resource_type(), gr.get_version_str(),
                   len(list(gr.get_files())),
                      sum([fs for _, fs, _ in gr.get_files()]), gr.get_id()))
    else:
        print(f'Unknown command {cmd}. The known commands are index and list')


if __name__ == '__main__':
    cli(sys.argv[1:])
