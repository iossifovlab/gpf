import { PhenoMeasure, PhenoMeasures } from "./pheno-browser"
import { environment } from '../../environments/environment';
  
export const fakeJsonMeasure = {
  Index: 1,
  instrument_name: 'test_instrument',
  values_domain: '0,1',
  figure_distribution: 'test.jpg',
  figure_distribution_small: null,
  figure_correlation_nviq: 'test_nviq.jpg',
  figure_correlation_nviq_small: 'test_nviq_small.jpg',
  pvalue_correlation_nviq_male: 0.000001,
  pvalue_correlation_nviq_female: 0.2,
  figure_correlation_age: 'test_age.jpg',
  figure_correlation_age_small: 'test_age_small.jpg',
  pvalue_correlation_age_male: 0.3,
  pvalue_correlation_age_female: 0.4,
  measure_id: 'test_instrument.test_measure',
  measure_name: 'test_measure',
  measure_type: 'ordinal',
  description: 'a test measure',
};

describe('pheno measure', () => {

  it('should be creatable from a given json', () => {

    let phenoMeasure = PhenoMeasure.fromJson(fakeJsonMeasure);

    expect(phenoMeasure.index).toBe(1);
    expect(phenoMeasure.instrumentName).toBe('test_instrument');
    expect(phenoMeasure.valuesDomain).toBe('0,1');
    expect(phenoMeasure.figureDistribution).toBe('test.jpg');
    expect(phenoMeasure.figureDistributionSmall).toBe(null);
    expect(phenoMeasure.figureCorrelationNviq).toBe('test_nviq.jpg');
    expect(phenoMeasure.figureCorrelationNviqSmall).toBe('test_nviq_small.jpg');
    expect(phenoMeasure.pvalueCorrelationNviqMale).toBe(0.000001);
    expect(phenoMeasure.pvalueCorrelationNviqFemale).toBe(0.2);
    expect(phenoMeasure.figureCorrelationAge).toBe('test_age.jpg');
    expect(phenoMeasure.figureCorrelationAgeSmall).toBe('test_age_small.jpg');
    expect(phenoMeasure.pvalueCorrelationAgeMale).toBe(0.3);
    expect(phenoMeasure.pvalueCorrelationAgeFemale).toBe(0.4);
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
    expect(bpMeasure.figureCorrelationNviq).toBe(environment.basePath + '/test_base_url/test_nviq.jpg');
    expect(bpMeasure.figureCorrelationNviqSmall).toBe(environment.basePath + '/test_base_url/test_nviq_small.jpg');
    expect(bpMeasure.figureCorrelationAge).toBe(environment.basePath + '/test_base_url/test_age.jpg');
    expect(bpMeasure.figureCorrelationAgeSmall).toBe(environment.basePath + '/test_base_url/test_age_small.jpg');
  });
});
