import os
import logging
import copy

import toml
from deprecation import deprecated  # type: ignore

from dae.studies.study import GenotypeDataStudy, GenotypeDataGroup
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.study_config import study_config_schema


logger = logging.getLogger(__name__)


DEFAULT_STUDY_CONFIG_TOML = """

has_denovo = true
has_transmitted = false
has_complex = false
has_cnv = false

phenotype_browser = false
phenotype_tool = false

[person_set_collections]
selected_person_set_collections = ["status"]

status.id = "status"
status.name = "Affected Status"
status.domain = [
    {
        id = "affected",
        name = "affected",
        values = ["affected"],
        color = "#e35252"
    },
    {
        id = "unaffected",
        name = "unaffected",
        values = ["unaffected"],
        color = "#ffffff"
    }
]
status.default = {id = "unspecified", name = "unspecified", values = [
    "unspecified"],color = "#aaaaaa"}
status.sources = [{
    from = "pedigree",
    source = "status"
}]

[genotype_browser]
enabled = true
has_family_filters = true
has_person_filters = true
has_study_filters = false
has_present_in_child = true
has_present_in_parent = true
has_pedigree_selector = true

preview_columns = [
	"family",
	"variant",
	"genotype",
	"effect",
	"gene_scores",
	"freq"
]

download_columns = [
	"family",
	"study_phenotype",
	"variant",
	"variant_extra",
	"family_person_ids",
	"family_structure",
	"best",
	"family_genotype",
	"carriers",
	"inheritance",
	"phenotypes",
	"par_called",
	"allele_freq",
	"effect",
	"geneeffect",
	"effectdetails",
	"gene_scores",
]

summary_preview_columns = ["variant", "effect", "scores", "freq"]
summary_download_columns = ["variant", "effect", "scores", "freq"]

[genotype_browser.column_groups]
effect.name = "effect"
effect.columns = ["worst_effect", "genes"]

gene_scores.name = "vulnerability/intolerance"
gene_scores.columns = ["lgd_rank", "rvis_rank", "pli_rank"]

family.name = "family"
family.columns = ["family_id", "study"]

variant.name = "variant"
variant.columns = ["location", "variant"]

variant_extra.name = "variant"
variant_extra.columns = ["chrom", "position", "reference", "alternative"]

carriers.name = "carriers"
carriers.columns = ["carrier_person_ids", "carrier_person_attributes"]

phenotypes.name = "phenotypes"
phenotypes.columns = ["family_phenotypes", "carrier_phenotypes"]

freq.name = "Frequency"
freq.columns = ["exome_gnomad_af_percent", "genome_gnomad_af_percent"]

[genotype_browser.columns.genotype]
genotype.name = "genotype"
genotype.source = "pedigree"

worst_effect.name = "worst effect"
worst_effect.source = "worst_effect"

genes.name = "genes"
genes.source = "genes"

lgd_rank.name = "LGD rank"
lgd_rank.source = "LGD_rank"
lgd_rank.format = "%%d"

rvis_rank.name="RVIS rank"
rvis_rank.source = "RVIS_rank"
rvis_rank.format="%%d"

pli_rank.name="pLI rank"
pli_rank.source="pLI_rank"
pli_rank.format="%%d"

family_id.name = "family id"
family_id.source = "family"

study.name = "study"
study.source = "study_name"

family_person_ids.name = "family person ids"
family_person_ids.source = "family_person_ids"

location.name = "location"
location.source = "location"

variant.name = "variant"
variant.source = "variant"

chrom.name = "CHROM"
chrom.source = "chrom"

position.name = "POS"
position.source = "position"

reference.name = "REF"
reference.source = "reference"

alternative.name = "ALT"
alternative.source = "alternative"

carrier_person_ids.name = "carrier person ids"
carrier_person_ids.source = "carrier_person_ids"

carrier_person_attributes.name = "carrier person attributes"
carrier_person_attributes.source = "carrier_person_attributes"

inheritance.name = "inheritance type"
inheritance.source = "inheritance_type"

family_phenotypes.name = "family phenotypes"
family_phenotypes.source = "family_phenotypes"

carrier_phenotypes.name = "carrier phenotypes"
carrier_phenotypes.source = "carrier_phenotypes"

study_phenotype.name = "study phenotype"
study_phenotype.source = "study_phenotype"

best.name = "family best state"
best.source = "best_st"

family_genotype.name = "family genotype"
family_genotype.source = "genotype"

family_structure.name = "family structure"
family_structure.source = "family_structure"

# VARIANT EFFECTS

geneeffect.name = "all effects"
geneeffect.source = "effects"

effectdetails.name = "effect details"
effectdetails.source = "effect_details"

# VARIANT FREQUENCY

alt_alleles.name = "alt alleles"
alt_alleles.source = "af_allele_count"

par_called.name = "parents called"
par_called.source = "af_parents_called_count"

allele_freq.name = "allele frequency"
allele_freq.source = "af_allele_freq"

# SUMMARY VARIANTS

seen_as_denovo.name = "seen_as_denovo"
seen_as_denovo.source = "seen_as_denovo"

seen_in_affected.name = "seen_in_affected"
seen_in_affected.source = "seen_in_affected"

seen_in_unaffected.name = "seen_in_unaffected"
seen_in_unaffected.source = "seen_in_unaffected"

[gene_browser]
enabled = true
frequency_column = "af_allele_freq"
effect_column = "effect.worst effect type"
location_column = "variant.location"
domain_min = 0.001
domain_max = 100


[common_report]
enabled = true
"""  # noqa


DEFAULT_STUDY_CONFIG = GPFConfigParser.parse_and_interpolate(
    DEFAULT_STUDY_CONFIG_TOML, parser=toml.loads)  # noqa


class VariantsDb:
    """Database responsible for keeping genotype data studies and groups."""

    def __init__(
            self,
            dae_config,
            genome,
            gene_models,
            genotype_storage_factory):

        self.dae_config = dae_config

        assert genome is not None
        assert gene_models is not None

        assert genotype_storage_factory is not None

        self.genome = genome
        self.gene_models = gene_models
        self.genotype_storage_factory = genotype_storage_factory

        self.reload()

    def reload(self):
        """Load all studies and groups again."""
        self._genotype_study_cache = {}
        self._genotype_group_cache = {}

        genotype_study_configs = self._load_study_configs()
        genotype_group_configs = self._load_group_configs()

        overlap = set(genotype_study_configs.keys()) & \
            set(genotype_group_configs.keys())
        if overlap:
            logger.error(
                "overlapping configurations for studies and groups: %s",
                overlap)
            raise ValueError(
                f"overlapping configurations for studies and groups: "
                f"{overlap}")

        self._load_all_genotype_studies(genotype_study_configs)
        self._load_all_genotype_groups(genotype_group_configs)

    def _load_study_configs(self):
        logger.info("loading study configs: %s", self.dae_config.studies)
        default_config_filename = None
        default_config = None

        if self.dae_config.default_study_config and \
                self.dae_config.default_study_config.conf_file:
            default_config_filename = \
                self.dae_config.default_study_config.conf_file

        if default_config_filename is None or \
                not os.path.exists(default_config_filename):
            logger.info(
                "default config file is missing: %s", default_config_filename)
            default_config_filename = None

        if default_config_filename is None:
            default_config = copy.deepcopy(DEFAULT_STUDY_CONFIG)

        if self.dae_config.studies is None or \
                self.dae_config.studies.dir is None:
            studies_dir = os.path.join(
                self.dae_config.conf_dir, "studies")
        else:
            studies_dir = self.dae_config.studies.dir

        study_configs = GPFConfigParser.load_directory_configs(
            studies_dir,
            study_config_schema,
            default_config_filename=default_config_filename,
            default_config=default_config
        )

        genotype_study_configs = {}
        for study_config in study_configs:
            assert study_config.id is not None, study_config
            if study_config.enabled is False:
                continue
            genotype_study_configs[study_config.id] = \
                study_config
        return genotype_study_configs

    def _load_group_configs(self):
        default_config_filename = None
        default_config = None

        if self.dae_config.default_study_config and \
                self.dae_config.default_study_config.conf_file:
            default_config_filename = \
                self.dae_config.default_study_config.conf_file

        if default_config_filename is None or \
                not os.path.exists(default_config_filename):
            logger.info(
                "default config file is missing: %s", default_config_filename)
            default_config_filename = None
        if default_config_filename is None:
            default_config = copy.deepcopy(DEFAULT_STUDY_CONFIG)

        if self.dae_config.datasets is None or \
                self.dae_config.datasets.dir is None:
            datasets_dir = os.path.join(
                self.dae_config.conf_dir, "datasets")
        else:
            datasets_dir = self.dae_config.datasets.dir

        group_configs = GPFConfigParser.load_directory_configs(
            datasets_dir,
            study_config_schema,
            default_config_filename=default_config_filename,
            default_config=default_config
        )

        genotype_group_configs = {}
        for group_config in group_configs:
            assert group_config.id is not None, group_config
            if group_config.enabled is False:
                continue
            genotype_group_configs[group_config.id] = \
                group_config
        return genotype_group_configs

    def get_genotype_study(self, study_id):
        # if study_id not in self._genotype_study_cache:
        #     study_configs = self._load_study_configs()
        #     if study_id not in study_configs:
        #         return None
        #     self._load_genotype_study(study_configs[study_id])
        return self._genotype_study_cache.get(study_id)

    def get_genotype_study_config(self, study_id):
        genotype_study = self.get_genotype_study(study_id)
        if genotype_study is None:
            return None
        return genotype_study.config

    def get_all_genotype_study_ids(self):
        return list(self._genotype_study_cache.keys())

    def get_all_genotype_study_configs(self):
        return [
            genotype_study.config
            for genotype_study in self._genotype_study_cache.values()
        ]

    def get_all_genotype_studies(self):
        return list(self._genotype_study_cache.values())

    def get_genotype_group(self, group_id):
        # if group_id not in self._genotype_group_cache:
        #     group_configs = self._load_group_configs()
        #     if group_id not in group_configs:
        #         return None
        #     self._load_genotype_group(group_configs[group_id])
        return self._genotype_group_cache.get(group_id)

    def get_genotype_group_config(self, group_id):
        genotype_group = self.get_genotype_group(group_id)
        if genotype_group is None:
            return None
        return genotype_group.config

    def get_all_genotype_group_ids(self):
        return list(self._genotype_group_cache.keys())

    def get_all_genotype_groups(self):
        return list(self._genotype_group_cache.values())

    def get_all_genotype_group_configs(self):
        return [
            genotype_group.config
            for genotype_group in self._genotype_group_cache.values()
        ]

    @deprecated(details="start using GPFInstance methods")
    def get_all_ids(self):
        return (
            self.get_all_genotype_study_ids()
            + self.get_all_genotype_group_ids()
        )

    @deprecated(details="start using GPFInstance methods")
    def get_config(self, config_id):
        study_config = self.get_genotype_study_config(config_id)
        genotype_data_group_config = self.get_genotype_group_config(
            config_id
        )
        return study_config if study_config else genotype_data_group_config

    @deprecated(details="start using GPFInstance methods")
    def get(self, object_id):
        genotype_data_study = self.get_genotype_study(object_id)
        genotype_data_group = self.get_genotype_group(object_id)
        return (
            genotype_data_study if genotype_data_study else genotype_data_group
        )

    @deprecated(details="start using GPFInstance methods")
    def get_all_genotype_data(self):
        group_studies = self.get_all_genotype_studies()
        genotype_data_groups = self.get_all_genotype_groups()
        return group_studies + genotype_data_groups

    def _load_all_genotype_studies(self, genotype_study_configs):
        if genotype_study_configs is None:
            genotype_study_configs = self._load_study_configs()

        for study_id, study_config in genotype_study_configs.items():
            if study_id not in self._genotype_study_cache:
                self._load_genotype_study(study_config)

    def _load_genotype_study(self, study_config):
        if not study_config:
            return None

        logger.info(
            "creating genotype study: %s", study_config.id)

        genotype_study = self._make_genotype_study(study_config)
        if genotype_study is None:
            logger.warning("unable to load a study <%s>", study_config.id)
            return None

        self._genotype_study_cache[study_config.id] = genotype_study
        return genotype_study

    def _make_genotype_study(self, study_config):
        if study_config is None:
            return None

        genotype_storage = self.genotype_storage_factory.get_genotype_storage(
            study_config.genotype_storage.id
        )

        if genotype_storage is None:
            storage_ids = (
                self.genotype_storage_factory.get_genotype_storage_ids()
            )
            logger.error(
                "unknown genotype storage id: %s; Known ones: %s",
                study_config.genotype_storage.id,
                storage_ids
            )
            return None

        try:
            variants = genotype_storage.build_backend(
                study_config, self.genome, self.gene_models
            )

            return GenotypeDataStudy(study_config, variants)
        except Exception as ex:  # pylint: disable=broad-except
            logger.error("unable to create study %s", study_config.id)
            logger.exception(ex)
            return None

    def _load_all_genotype_groups(self, genotype_group_configs=None):
        if genotype_group_configs is None:
            genotype_group_configs = self._load_group_configs()

        for group_id, group_config in genotype_group_configs.items():
            if group_id not in self._genotype_group_cache:
                self._load_genotype_group(group_config)

    def _load_genotype_group(self, group_config):
        if group_config is None:
            return None

        logger.info(
            "creating genotype group: %s", group_config.id)
        try:
            group_studies = []
            for child_id in group_config.studies:
                logger.info("looking for a child: %s", child_id)
                if child_id in self._genotype_study_cache:
                    child_data = self.get_genotype_study(child_id)
                    assert child_data is not None, child_id
                else:
                    child_data = self.get_genotype_group(child_id)
                    if child_data is None:
                        # group not loaded... load it...
                        logger.info(
                            "child genotype data %s not found; "
                            "trying to create it...",
                            child_id
                        )
                        genotype_group_configs = self._load_group_configs()
                        child_config = genotype_group_configs[child_id]
                        child_data = self._load_genotype_group(child_config)

                group_studies.append(child_data)
            assert group_studies

            genotype_group = GenotypeDataGroup(group_config, group_studies)
            self._genotype_group_cache[group_config.id] = genotype_group
            return genotype_group

        except Exception as ex:  # pylint: disable=broad-except
            logger.error(
                "unable to create genotype data group %s", group_config.id)
            logger.exception(ex)
            return None

    def register_genotype_data(self, genotype_data):
        """Add GenotypeData to DB."""
        if genotype_data.study_id in self.get_all_genotype_study_ids():
            logger.warning(
                "replacing genotype study instance %s", genotype_data.study_id)
        if genotype_data.study_id in self.get_all_genotype_group_ids():
            logger.warning(
                "replacing genotype group instance %s", genotype_data.study_id)

        if genotype_data.is_group:
            self._genotype_group_cache[genotype_data.study_id] = genotype_data
        else:
            self._genotype_study_cache[genotype_data.study_id] = genotype_data

    def unregister_genotype_data(self, genotype_data):
        """Remove GenotypeData from DB."""
        if genotype_data.is_group:
            self._genotype_group_cache.pop(genotype_data.study_id)
        else:
            self._genotype_study_cache.pop(genotype_data.study_id)
