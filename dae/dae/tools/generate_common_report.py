#!/usr/bin/env python
import time
import argparse

from dae.gpf_instance.gpf_instance import GPFInstance


def main(gpf_instance=None, argv=None):
    description = "Generate common reports tool"
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "--show-studies",
        help="This option will print available "
        "genotype studies and groups names",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "--studies",
        help="Specify genotype studies and groups "
        "names for generating common report. Default to all query objects.",
        default=None,
        action="store",
    )

    args = parser.parse_args(argv)
    start = time.time()
    if gpf_instance is None:
        gpf_instance = GPFInstance()

    common_report_facade = gpf_instance._common_report_facade

    if args.show_studies:
        for study_id in common_report_facade.get_all_common_report_ids():
            print(study_id)
    else:
        elapsed = time.time() - start
        print(f"started common reports generation after {elapsed:0.2f} sec")
        if args.studies:
            studies = args.studies.split(",")
            print("generating common reports for:", studies)
            common_report_facade.generate_common_reports(studies)
        else:
            print("generating common reports for all studies!!!")
            common_report_facade.generate_all_common_reports()


if __name__ == "__main__":
    main()
