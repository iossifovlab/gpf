import argparse
import os
import shutil

from generate_configs import ConfigGenerator


def export_histograms(scores_dir, output_dir):
    scores_dir = os.path.abspath(scores_dir)
    output_dir = os.path.abspath(output_dir)
    assert os.path.exists(scores_dir)
    assert os.path.exists(output_dir)

    for directory in os.walk(scores_dir):
        if os.path.basename(directory[0]) == 'histograms':
            for file_ in directory[2]:
                shutil.copy2(os.path.join(directory[0], file_),
                             os.path.join(output_dir, file_))


if __name__ == '__main__':
    parser = \
        argparse.ArgumentParser(description=('Export histograms from a genomic'
                                             ' scores repository to a given'
                                             ' folder.'))
    group = parser.add_mutually_exclusive_group()
    parser.add_argument('output_dir',
                        help='directory to export histograms into')
    group.add_argument('--annotation_config',
                       help='annotation pipeline config to use')
    group.add_argument('--genomic_scores_repo',
                       help='genomic scores repository to use')
    args = parser.parse_args()

    assert args.annotation_config or args.genomic_scores_repo, \
        ('You must provide either a genomic scores repository'
         'or an annotation pipeline configuration.')

    if args.annotation_config:
        config_gen = ConfigGenerator(args.config)
        dirs = list(config_gen.pipeline_config.score_dirs)
    else:
        dirs = [args.genomic_scores_repo]

    for dir_ in dirs:
        export_histograms(dir_, args.output_dir)
