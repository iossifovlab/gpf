#!/usr/bin/env python
from studies.factory import VariantsDb
from configurable_entities.configuration import DAEConfig


def main(dae_config=None):
    dae_config = DAEConfig()
    vdb = VariantsDb(dae_config)
    crg = vdb.common_reports_generator
    crg.save_common_reports()


if __name__ == '__main__':
    main()
