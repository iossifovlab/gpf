from dae.variants.attributes import Sex
from collections import Counter


class PhenoToolAdapterBase:
    def calc_variants(self, data):
        raise NotImplementedError()


class PhenoToolAdapter(PhenoToolAdapterBase):
    def __init__(self, study_wrapper, pheno_tool, pheno_tool_helper):
        self.study_wrapper = study_wrapper
        self.pheno_tool = pheno_tool
        self.helper = pheno_tool_helper

    def get_result_by_sex(self, result, sex):
        return {
            "negative": {
                "count": result[sex].negative_count,
                "deviation": result[sex].negative_deviation,
                "mean": result[sex].negative_mean,
            },
            "positive": {
                "count": result[sex].positive_count,
                "deviation": result[sex].positive_deviation,
                "mean": result[sex].positive_mean,
            },
            "pValue": result[sex].pvalue,
        }

    def calc_by_effect(self, effect, people_variants):
        result = self.pheno_tool.calc(people_variants, sex_split=True)
        return {
            "effect": effect,
            "maleResults": self.get_result_by_sex(result, Sex.M.name),
            "femaleResults": self.get_result_by_sex(result, Sex.F.name),
        }

    @staticmethod
    def align_NA_results(results):
        for result in results:
            for sex in ["femaleResults", "maleResults"]:
                res = result[sex]
                if res["positive"]["count"] == 0:
                    assert res["positive"]["mean"] == 0
                    assert res["positive"]["deviation"] == 0
                    assert res["pValue"] == "NA"
                    res["positive"]["mean"] = res["negative"]["mean"]
                if res["negative"]["count"] == 0:
                    assert res["negative"]["mean"] == 0
                    assert res["negative"]["deviation"] == 0
                    assert res["pValue"] == "NA"
                    res["negative"]["mean"] = res["positive"]["mean"]

    def build_report_description(self):
        normalize_by = self.pheno_tool.normalize_by
        measure_id = self.pheno_tool.measure_id
        if not normalize_by:
            return measure_id
        else:
            return "{} ~ {}".format(measure_id, " + ".join(normalize_by))

    def calc_variants(self, data):
        data = self.study_wrapper.transform_request(data)
        people_variants = self.helper.genotype_data_variants(data)

        results = [
            self.calc_by_effect(
                effect, people_variants.get(effect.lower(), Counter())
            )
            for effect in data["effect_types"]
        ]
        self.align_NA_results(results)

        output = {
            "description": self.build_report_description(),
            "results": results,
        }

        return output


class RemotePhenoToolAdapter(PhenoToolAdapterBase):
    def __init__(self, rest_client, dataset_id):
        self.rest_client = rest_client
        self.dataset_id = dataset_id

    def calc_variants(self, data):
        data["datasetId"] = self.dataset_id
        return self.rest_client.post_pheno_tool(data)
