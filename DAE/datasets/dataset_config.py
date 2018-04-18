import os
import reusables
from box import ConfigBox

from datasets.config_old import PedigreeSelector


class DatasetConfig(ConfigBox):

    def __init__(self, *args, **kwargs):
        super(DatasetConfig, self).__init__(*args, **kwargs)
        assert self.dataset_name
        assert self.variants_prefix
        assert self.preview_columns
        assert self.download_columns

        print("download_columns", self.list('preview_columns'))
        print("download_columns", self.list('download_columns'))

    @staticmethod
    def from_config(path, work_dir=None):
        if work_dir is None:
            from default_settings import DATA_DIR
            work_dir = DATA_DIR
        assert os.path.exists(path)

        config = reusables.config_dict(
            path,
            auto_find=False,
            verify=True,
            defaults={
                'wd': work_dir,
            }
        )

        return DatasetConfig(config['dataset'])

    def get_dataset_description(self):
        return {
            "phenotypeGenotypeTool": True,
            "phenotypeBrowser": True,
            "description": "Description",
            "studies": "SPARK",
            "studyTypes": None,
            "phenoDB": "spark",
            "genotypeBrowser": {
                "hasPedigreeSelector": False, # to prevent counters from loading
                "genesBlockShowAll": True,
                "hasPresentInChild": True,
                "downloadColumns": ["family", "phenotype", "variant", "best",
                                    "fromparent", "inchild", "effect", "count",
                                    "geneeffect", "effectdetails", "weights",
                                    "freq", "scores"],
                "phenoColumns": [{
                                     "slots": [{
                                                   "source": "scq.summary_score",
                                                   "role": "prb",
                                                   "name": "Summary",
                                                   "id": "prb.scq.summary_score"
                                               }, {
                                                   "source": "scq.final_score",
                                                   "role": "prb",
                                                   "name": "Final",
                                                   "id": "prb.scq.final_score"
                                               }],
                                     "id": "scores",
                                     "name": "SCQ Scores"
                                 }],
                "hasFamilyFilters": False,
                "hasDenovo": True,
                "familyStudyFilters": None,
                "mainForm": "default",
                "phenoFilters": [{
                                     "measureType": "continuous",
                                     "measureFilter": {
                                         "filterType": "multi",
                                         "role": "prb"
                                     },
                                     "name": "Proband Continuous"
                                 }],
                "hasPresentInParent": True,
                "hasStudyTypes": False,
                "hasComplex": False,
                "genotypeColumns": [{
                                        "source": None,
                                        "slots": [{
                                                      "id": "familyId",
                                                      "source": "familyId",
                                                      "name": "family id",
                                                      "format": "%s"
                                                  }, {
                                                      "id": "studyName",
                                                      "source": "studyName",
                                                      "name": "study",
                                                      "format": "%s"
                                                  }],
                                        "id": "family",
                                        "name": "family"
                                    }, {
                                        "source": "_phenotype_",
                                        "slots": [],
                                        "id": "phenotype",
                                        "name": "study phenotype"
                                    }, {
                                        "source": None,
                                        "slots": [{
                                                      "id": "location",
                                                      "source": "location",
                                                      "name": "location",
                                                      "format": "%s"
                                                  }, {
                                                      "id": "variant",
                                                      "source": "variant",
                                                      "name": "variant",
                                                      "format": "%s"
                                                  }],
                                        "id": "variant",
                                        "name": "variant"
                                    }, {
                                        "source": "bestSt",
                                        "slots": [],
                                        "id": "best",
                                        "name": "family genotype"
                                    }, {
                                        "source": "fromParentS",
                                        "slots": [],
                                        "id": "fromparent",
                                        "name": "from parent"
                                    }, {
                                        "source": "inChS",
                                        "slots": [],
                                        "id": "inchild",
                                        "name": "in child"
                                    }, {
                                        "source": "pedigree",
                                        "slots": [{
                                                      "id": "inChS",
                                                      "source": "inChS",
                                                      "name": "in child",
                                                      "format": "%s"
                                                  }, {
                                                      "id": "fromParentS",
                                                      "source": "fromParentS",
                                                      "name": "from parent",
                                                      "format": "%s"
                                                  }],
                                        "id": "genotype",
                                        "name": "genotype"
                                    }, {
                                        "source": None,
                                        "slots": [{
                                                      "id": "effectType",
                                                      "source": "effectType",
                                                      "name": "worst effect type",
                                                      "format": "%s"
                                                  }, {
                                                      "id": "genes",
                                                      "source": "genes",
                                                      "name": "genes",
                                                      "format": "%s"
                                                  }],
                                        "id": "effect",
                                        "name": "effect"
                                    }, {
                                        "source": "counts",
                                        "slots": [],
                                        "id": "count",
                                        "name": "count"
                                    }, {
                                        "source": "geneEffect",
                                        "slots": [],
                                        "id": "geneeffect",
                                        "name": "all effects"
                                    }, {
                                        "source": "effectDetails",
                                        "slots": [],
                                        "id": "effectdetails",
                                        "name": "effect details"
                                    }, {
                                        "source": None,
                                        "slots": [{
                                                      "id": "LGD_rank",
                                                      "source": "LGD_rank",
                                                      "name": "LGD rank",
                                                      "format": "LGD %d"
                                                  }, {
                                                      "id": "RVIS_rank",
                                                      "source": "RVIS_rank",
                                                      "name": "RVIS rank",
                                                      "format": "RVIS %d"
                                                  }, {
                                                      "id": "pLI_rank",
                                                      "source": "pLI_rank",
                                                      "name": "pLI rank",
                                                      "format": "pLI %d"
                                                  }],
                                        "id": "weights",
                                        "name": "vulnerability/intolerance"
                                    }, {
                                        "source": None,
                                        "slots": [{
                                                      "id": "SSC-freq",
                                                      "source": "SSC-freq",
                                                      "name": "SSC",
                                                      "format": "SSC %.2f %%"
                                                  }, {
                                                      "id": "EVS-freq",
                                                      "source": "EVS-freq",
                                                      "name": "EVS",
                                                      "format": "EVS %.2f %%"
                                                  }, {
                                                      "id": "E65-freq",
                                                      "source": "E65-freq",
                                                      "name": "E65",
                                                      "format": "E65 %.2f %%"
                                                  }],
                                        "id": "freq",
                                        "name": "allele freq"
                                    }],
                "hasTransmitted": True,
                "previewColumns": ["family", "variant", "genotype", "effect",
                                   "weights", "freq", "scores"],
                "hasCNV": True,
                "genomicMetrics": [{
                                       "id": "SSC-freq",
                                       "name": "SSC"
                                   }, {
                                       "id": "EVS-freq",
                                       "name": "EVS"
                                   }, {
                                       "id": "E65-freq",
                                       "name": "E65"
                                   }]
            },
            "enrichmentTool": {
                "studyTypes": ["WE"],
                "selector": "phenotype"
            },
            "authorizedGroups": ["SIMONS"],
            "pedigreeSelectors": [{
                                      "domain": [{
                                                     "color": "#e35252",
                                                     "id": "autism",
                                                     "name": "autism"
                                                 }, {
                                                     "color": "#ffffff",
                                                     "id": "unaffected",
                                                     "name": "unaffected"
                                                 }],
                                      "name": "Phenotype",
                                      "default": {
                                          "color": "#aaaaaa",
                                          "id": "unknown",
                                          "name": "unknown"
                                      },
                                      "source": "legacy",
                                      "values": {
                                          "unaffected": {
                                              "color": "#ffffff",
                                              "id": "unaffected",
                                              "name": "unaffected"
                                          },
                                          "autism": {
                                              "color": "#e35252",
                                              "id": "autism",
                                              "name": "autism"
                                          }
                                      },
                                      "id": "phenotype"
                                  }],
            "id": "SPARK",
            "name": "SPARK Dataset"
        }
