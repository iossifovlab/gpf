import { PhenoMeasure, PhenoMeasures, PhenoRegression, PhenoRegressions } from './pheno-browser';
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
      regression_id: 'age',
      measure_id: 'test_instrument.test_measure',
      figure_regression: 'imagepath',
      figure_regression_small: 'imagepathsmall',
      pvalue_regression_male: 1.0e-6,
      pvalue_regression_female: 0.20,
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
      regression_id: 'age',
      measure_id: 'test_instrument.test_measure',
      figure_regression: 'imagepathage',
      figure_regression_small: 'imagepathagesmall',
      pvalue_regression_male: 0.01,
      pvalue_regression_female: 1.0,
    },
    {
      regression_id: 'iq',
      measure_id: 'test_instrument.test_measure',
      figure_regression: 'imagepathiq',
      figure_regression_small: 'imagepathiqsmall',
      pvalue_regression_male: 0.02,
      pvalue_regression_female: 2.0,
    }
  ]
};

describe('pheno measure', () => {
  it('should be creatable from a given json', () => {
    const phenoMeasure = PhenoMeasure.fromJson(fakeJsonMeasure);
    expect(phenoMeasure.index).toBe(1);
    expect(phenoMeasure.instrumentName).toBe('test_instrument');
    expect(phenoMeasure.valuesDomain).toBe('0,1');
    expect(phenoMeasure.figureDistribution).toBe('test.jpg');
    expect(phenoMeasure.figureDistributionSmall).toBeNull();
    expect(phenoMeasure.measureId).toBe('test_instrument.test_measure');
    expect(phenoMeasure.measureName).toBe('test_measure');
    expect(phenoMeasure.measureType).toBe('ordinal');
    expect(phenoMeasure.description).toBe('a test measure');
  });
});

describe('pheno measures', () => {
  const basePath = '/test_base_url/';
  let phenoMeasure = PhenoMeasure.fromJson(fakeJsonMeasure);

  phenoMeasure = PhenoMeasure.addBasePath(phenoMeasure, basePath);

  const phenoMeasures = PhenoMeasures.fromJson({
    /* eslint-disable @typescript-eslint/naming-convention */
    base_image_url: basePath,
    measures: [fakeJsonMeasure],
    has_descriptions: true
    /* eslint-enable */

  });

  it('should be creatable from a given json', () => {
    expect(phenoMeasures.baseImageUrl).toBe('/test_base_url/');
    expect(phenoMeasures.measures[0]).toStrictEqual(phenoMeasure);
    expect(phenoMeasures.hasDescriptions).toBe(true);
  });

  it('should be able to add a base path', () => {
    const bpMeasures = phenoMeasures;
    const bpMeasure = bpMeasures.measures[0];
    expect(bpMeasure.figureDistribution).toBe(environment.basePath + '/test_base_url/test.jpg');
    expect(bpMeasure.figureDistributionSmall).toBeNull();
  });
});

describe('PhenoRegression', () => {
  const phenoRegression = new PhenoRegression(fakeJsonMeasureOneRegression.regressions[0]);
  const phenoRegressionBasePath = new PhenoRegression(fakeJsonMeasureOneRegression.regressions[0]);

  it('should be creatable from a given json', () => {
    expect(phenoRegression.regressionId).toBe('age');
    expect(phenoRegression.measureId).toBe('test_instrument.test_measure');
    expect(phenoRegression.figureRegression).toBe('imagepath');
    expect(phenoRegression.figureRegressionSmall).toBe('imagepathsmall');
    expect(phenoRegression.pvalueRegressionMale).toBe(1.0e-6);
    expect(phenoRegression.pvalueRegressionFemale).toBe(0.20);
  });

  it('should be able to add a base path', () => {
    phenoRegressionBasePath.addBasePath('a_base_path/');
    expect(phenoRegressionBasePath.figureRegression).toBe('a_base_path/imagepath');
    expect(phenoRegressionBasePath.figureRegressionSmall).toBe('a_base_path/imagepathsmall');
  });
});

describe('PhenoRegressions', () => {
  const phenoRegressions = new PhenoRegressions(fakeJsonMeasureTwoRegressions.regressions);
  const phenoRegressionsBasePath = new PhenoRegressions(fakeJsonMeasureTwoRegressions.regressions);

  it('should be creatable from a given json', () => {
    expect((phenoRegressions['age'] as PhenoRegression).regressionId).toBe('age');
    expect((phenoRegressions['age'] as PhenoRegression).measureId).toBe('test_instrument.test_measure');
    expect((phenoRegressions['age'] as PhenoRegression).figureRegression).toBe('imagepathage');
    expect((phenoRegressions['age'] as PhenoRegression).figureRegressionSmall).toBe('imagepathagesmall');
    expect((phenoRegressions['age'] as PhenoRegression).pvalueRegressionMale).toBe(0.01);
    expect((phenoRegressions['age'] as PhenoRegression).pvalueRegressionFemale).toBe(1.00);

    expect((phenoRegressions['iq'] as PhenoRegression).regressionId).toBe('iq');
    expect((phenoRegressions['iq'] as PhenoRegression).measureId).toBe('test_instrument.test_measure');
    expect((phenoRegressions['iq'] as PhenoRegression).figureRegression).toBe('imagepathiq');
    expect((phenoRegressions['iq'] as PhenoRegression).figureRegressionSmall).toBe('imagepathiqsmall');
    expect((phenoRegressions['iq'] as PhenoRegression).pvalueRegressionMale).toBe(0.02);
    expect((phenoRegressions['iq'] as PhenoRegression).pvalueRegressionFemale).toBe(2.00);
  });

  it('should be able to add a base path', () => {
    phenoRegressionsBasePath.addBasePath('a_base_path/');
    expect((phenoRegressionsBasePath['age'] as PhenoRegression).figureRegression).toBe('a_base_path/imagepathage');
    expect((phenoRegressionsBasePath['age'] as PhenoRegression).figureRegressionSmall)
      .toBe('a_base_path/imagepathagesmall');
    expect((phenoRegressionsBasePath['iq'] as PhenoRegression).figureRegression).toBe('a_base_path/imagepathiq');
    expect((phenoRegressionsBasePath['iq'] as PhenoRegression).figureRegressionSmall)
      .toBe('a_base_path/imagepathiqsmall');
  });
});
