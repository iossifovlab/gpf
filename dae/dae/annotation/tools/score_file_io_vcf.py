import logging
import cyvcf2

import pysam


logger = logging.getLogger(__name__)


class VcfInfoLineAdapter:
    def __init__(self, accessor, variant):
        self.accessor = accessor
        self.score_file = self.accessor.score_file
        self.variant = variant

    @property
    def pos_begin(self):
        return self.variant.POS

    @property
    def pos_end(self):
        return self.variant.POS

    @property
    def chrom(self):
        return self.variant.CHROM

    def get(self, name):
        if name == "ID":
            return self.variant.ID
        elif name == "CHROM":
            return self.variant.CHROM
        elif name == "POS":
            return self.variant.POS
        elif name == "REF":
            return self.variant.REF
        elif name == "ALT":
            return self.variant.ALT[0]
        elif name in self.accessor.info:
            return self.variant.INFO.get(name)
        elif name in self.accessor.extra:
            return self.accessor.extra[name](self.variant)
        logger.error(f"can not find {name} in {self.variant}")
        raise ValueError(f"can not find {name} in {self.variant}")

    def __getitem__(self, index):
        if index == 0:
            return self.chrom
        elif index == 1:
            return self.pos_begin
        else:
            name = self.score_file.header[index]
            return self.get(name)


class VcfInfoAccess:
    def __init__(self, score_file, filename=None):
        logger.debug(f"options: {score_file}, {dir(score_file)}")
        self.score_file = score_file
        if filename is None:
            assert self.score_file.score_filename is not None
            filename = self.score_file.score_filename

        self.score_filename = filename
        logger.debug(f"going to access VCF file {self.score_filename}")
        self.vcf = cyvcf2.VCF(self.score_filename)
        self.info = {}
        for h in self.vcf.header_iter():
            if h["HeaderType"] == "INFO":
                score_id = h["ID"]
                score_desc = h["Description"]
                score_type = h["Type"]
                self.info[score_id] = {
                    "id": score_id,
                    "desc": score_desc,
                    "type": score_type
                }
        self.extra = {}

        logger.debug(f"score names: {self.score_file.score_names}")
        failed = []
        for col_name in self.score_file.score_names:
            if col_name in self.info:
                continue
            if col_name.endswith("_percent"):
                base_col_name = col_name[:-len("_percent")]
                print(base_col_name)
                if base_col_name in self.info:
                    def percent(v):
                        base_val = v.INFO.get(base_col_name)
                        if base_val is None:
                            return None
                        else:
                            return 100.0 * base_val
                    self.extra[col_name] = percent
                    continue

            logger.error(
                f"score {col_name} missing in VCF info of {filename}")
            failed.append(col_name)
        if failed:
            raise ValueError(f"missing columns {failed} in VCF info")

    def _cleanup(self):
        self.vcf.close()
        self.vcf = None

    def _fetch(self, chrom, pos_begin, pos_end):
        assert pos_begin - 1 >= 0
        assert pos_end >= pos_begin

        region = f"{chrom}:{pos_begin}-{pos_end}"
        logger.debug(f"fetching region {region}")
        vcf_iterator = self.vcf(region)

        result = []
        for v in vcf_iterator:
            logger.debug(f"vcf variant: {v.CHROM}, {v.POS}")
            result.append(VcfInfoLineAdapter(self, v))

        return result
