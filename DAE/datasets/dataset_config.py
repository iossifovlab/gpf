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
        assert self.data_dir

        print("download_columns", self.list('preview_columns'))
        print("download_columns", self.list('download_columns'))

    @staticmethod
    def from_config(path, work_dir=None):
        if work_dir is None:
            from datasets.default_settings import DATA_DIR
            work_dir = DATA_DIR
        if not os.path.exists(path):
            path = os.path.join(work_dir, path)
        assert os.path.exists(path), path

        config = reusables.config_dict(
            path,
            auto_find=False,
            verify=True,
            defaults={
                'wd': work_dir,
            }
        )

        result = DatasetConfig(config['dataset'])
        if not os.path.isabs(result.variants_prefix):
            result.variants_prefix = os.path.join(
                result.data_dir, result.variants_prefix)

        return result

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
                "phenoColumns": [],
                "hasFamilyFilters": False,
                "hasDenovo": True,
                "familyStudyFilters": None,
                "mainForm": "default",
                "phenoFilters": [],
                "hasPresentInParent": True,
                "hasStudyTypes": False,
                "hasComplex": False,
                "genotypeColumns": [{
                                        "source": None,
                                        "slots": [{
                                                      "id": "family",
                                                      "source": "family",
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
                                                      "id": "worstEffect",
                                                      "source": "worstEffect",
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
                                    }],
                "hasTransmitted": True,
                "previewColumns": ["family", "variant", "genotype", "effect"],
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
