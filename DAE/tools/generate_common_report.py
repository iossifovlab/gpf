#!/usr/bin/env python
import argparse
from box import Box

from common_reports.common_report import CommonReportsGenerator
from common_reports.config import CommonReportsConfig


def main():
    desc = """Program to generate common reports"""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        '--config', action='store', default=None,
        help='Config file location. Default is get from environment.')

    opts = parser.parse_args()

    if opts.config is not None:
        crc = CommonReportsConfig(Box({'commonReportsConfFile': opts.config}))
    else:
        crc = CommonReportsConfig()

    crg = CommonReportsGenerator(crc)
    crg.save_common_reports()


if __name__ == '__main__':
    main()
