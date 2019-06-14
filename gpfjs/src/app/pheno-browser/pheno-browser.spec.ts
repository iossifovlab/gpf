import { PhenoMeasure, PhenoMeasures } from "./pheno-browser"
import { environment } from '../../environments/environment';
  
export const fakeJsonMeasure = {
  Index: 1,
  instrument_name: 'test_instrument',
  values_domain: '0,1',
  figure_distribution: 'test.jpg',
  figure_distribution_small: null,
  measure_id: 'test_instrument.test_measure',
  measure_name: 'test_measure',
  measure_type: 'ordinal',
  description: 'a test measure',
  regressions: []
};

export const fakeJsonMeasureOneRegression = {
  Index: 1,
  instrument_name: 'test_instrument',
  values_domain: '0,1',
  figure_distribution: 'test.jpg',
  figure_distribution_small: null,
  measure_id: 'test_instrument.test_measure',
  measure_name: 'test_measure',
  measure_type: 'ordinal',
  description: 'a test measure',
  regressions: [
    {
      regression_name: "age",
      measure_id: "test_instrument.test_measure",
      regression_measure_id: "test_instrument.age",
      figure_regression: "",
      figure_regression_small: "",
      pvalue_regression_male: "1.0e-6",
      pvalue_regression_female: "0.20",
    }
  ]
};

export const fakeJsonMeasureTwoRegressions = {
  Index: 1,
  instrument_name: 'test_instrument',
  values_domain: '0,1',
  figure_distribution: 'test.jpg',
  figure_distribution_small: null,
  measure_id: 'test_instrument.test_measure',
  measure_name: 'test_measure',
  measure_type: 'ordinal',
  description: 'a test measure',
  regressions: [
    {
      regression_name: "age",
      measure_id: "test_instrument.test_measure",
      regression_measure_id: "test_instrument.age",
      figure_regression: "",
      figure_regression_small: "",
      pvalue_regression_male: 0.01,
      pvalue_regression_female: 1.0,
    },
    {
      regression_name: "iq",
      measure_id: "test_instrument.test_measure",
      regression_measure_id: "test_instrument.nviq",
      figure_regression: "",
      figure_regression_small: "",
      pvalue_regression_male: 0.02,
      pvalue_regression_female: 2.0,
    }
  ]
}

describe('pheno measure', () => {

  it('should be creatable from a given json', () => {

    let phenoMeasure = PhenoMeasure.fromJson(fakeJsonMeasure);

    expect(phenoMeasure.index).toBe(1);
    expect(phenoMeasure.instrumentName).toBe('test_instrument');
    expect(phenoMeasure.valuesDomain).toBe('0,1');
    expect(phenoMeasure.figureDistribution).toBe('test.jpg');
    expect(phenoMeasure.figureDistributionSmall).toBe(null);
    expect(phenoMeasure.measureId).toBe('test_instrument.test_measure')
    expect(phenoMeasure.measureName).toBe('test_measure')
    expect(phenoMeasure.measureType).toBe('ordinal')
    expect(phenoMeasure.description).toBe('a test measure')
  });
});

describe('pheno measures', () => {
    
  let phenoMeasure = PhenoMeasure.fromJson(fakeJsonMeasure);

  let phenoMeasures = PhenoMeasures.fromJson({
    'base_image_url': '/test_base_url/',
    'measures': [fakeJsonMeasure],
    'has_descriptions': true,
  });

  it('should be creatable from a given json', () => {
    expect(phenoMeasures.baseImageUrl).toBe('/test_base_url/');
    expect(phenoMeasures.measures[0]).toEqual(phenoMeasure);
    expect(phenoMeasures.hasDescriptions).toBe(true);
  });

  it('should be able to add a base path', () => {
    let bpMeasures = PhenoMeasures.addBasePath(phenoMeasures);
    let bpMeasure = bpMeasures.measures[0];
    expect(bpMeasure.figureDistribution).toBe(environment.basePath + '/test_base_url/test.jpg');
    expect(bpMeasure.figureDistributionSmall).toBe(null);
  });
});
