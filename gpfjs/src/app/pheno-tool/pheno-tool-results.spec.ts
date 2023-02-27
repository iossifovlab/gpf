import {
  PhenoToolResult, PhenoToolResults, PhenoToolResultsPerEffect, PhenoToolResultsPerGender
} from './pheno-tool-results';

const [
  phenoToolResultsPerGenderJson1,
  phenoToolResultsPerGenderJson2,
  phenoToolResultsPerGenderJson3,
  phenoToolResultsPerGenderJson4
] = [
  {
    positive: {
      count: 1,
      deviation: 2,
      mean: 3
    }, negative: {
      count: 4,
      deviation: 5,
      mean: 6
    }, pValue: 7
  },
  {
    positive: {
      count: 8,
      deviation: 9,
      mean: 10
    }, negative: {
      count: 11,
      deviation: 12,
      mean: 13
    }, pValue: 14
  },
  {
    positive: {
      count: 15,
      deviation: 16,
      mean: 17
    }, negative: {
      count: 18,
      deviation: 19,
      mean: 20
    }, pValue: 21
  },
  {
    positive: {
      count: 22,
      deviation: 23,
      mean: 24
    }, negative: {
      count: 25,
      deviation: 26,
      mean: 27
    }, pValue: 28
  }
];

const [
  phenoToolResultsPerGender1,
  phenoToolResultsPerGender2,
  phenoToolResultsPerGender3,
  phenoToolResultsPerGender4
] = [
  new PhenoToolResultsPerGender(
    new PhenoToolResult(1, 2, 3),
    new PhenoToolResult(4, 5, 6), 7
  ),
  new PhenoToolResultsPerGender(
    new PhenoToolResult(8, 9, 10),
    new PhenoToolResult(11, 12, 13), 14
  ),
  new PhenoToolResultsPerGender(
    new PhenoToolResult(15, 16, 17),
    new PhenoToolResult(18, 19, 20), 21
  ),
  new PhenoToolResultsPerGender(
    new PhenoToolResult(22, 23, 24),
    new PhenoToolResult(25, 26, 27), 28
  )
];

const phenoToolEffectArrayJson1 = [
  {
    effect: 'effectType1',
    maleResults: phenoToolResultsPerGenderJson1,
    femaleResults: phenoToolResultsPerGenderJson2
  }, {
    effect: 'effectType2',
    maleResults: phenoToolResultsPerGenderJson3,
    femaleResults: phenoToolResultsPerGenderJson4
  }
];

const phenoToolEffectArray1 = [
  new PhenoToolResultsPerEffect(
    'effectType1',
    phenoToolResultsPerGender1,
    phenoToolResultsPerGender2
  ),
  new PhenoToolResultsPerEffect(
    'effectType2',
    phenoToolResultsPerGender3,
    phenoToolResultsPerGender4
  )
];

const phenoToolResultsPerEffectJson1 = {
  effect: 'effectType1',
  maleResults: phenoToolResultsPerGenderJson1,
  femaleResults: phenoToolResultsPerGenderJson2
};

const phenoToolResultsPerEffect1 = new PhenoToolResultsPerEffect(
  'effectType1',
  phenoToolResultsPerGender1,
  phenoToolResultsPerGender2
);

describe('PhenoToolResult', () => {
  it('should create from json', () => {
    const phenoToolFromJson = PhenoToolResult.fromJson({
      count: 5,
      deviation: 3,
      mean: 4
    });
    expect(phenoToolFromJson).toStrictEqual(new PhenoToolResult(5, 3, 4));
  });

  it('should get range start', () => {
    expect(new PhenoToolResult(6, 3, 4).rangeStart).toBe(1);
  });

  it('should get range end', () => {
    expect(new PhenoToolResult(5, 3, 4).rangeEnd).toBe(7);
  });
});

describe('PhenoToolResultsPerGender', () => {
  it('should create from json', () => {
    const phenoToolResultsPerGenderFromJson = PhenoToolResultsPerGender.fromJson(phenoToolResultsPerGenderJson1);
    expect(phenoToolResultsPerGender1).toStrictEqual(phenoToolResultsPerGenderFromJson);
  });
});

describe('PhenoToolResultsPerEffect', () => {
  it('should create from json', () => {
    const phenoToolResultsPerEffectFromJson = PhenoToolResultsPerEffect.fromJson(phenoToolResultsPerEffectJson1);
    expect(phenoToolResultsPerEffect1).toStrictEqual(phenoToolResultsPerEffectFromJson);
  });

  it('should create from json array', () => {
    const phenoToolEffectFromJsonArrayMock = PhenoToolResultsPerEffect.fromJsonArray(phenoToolEffectArrayJson1);
    expect(phenoToolEffectArray1).toStrictEqual(phenoToolEffectFromJsonArrayMock);
  });
});

describe('PhenoToolResults', () => {
  it('should create from json', () => {
    const phenoResultsMock = new PhenoToolResults('desc1', phenoToolEffectArray1);
    const phenoResultsMockFromJson = PhenoToolResults.fromJson({
      description: 'desc1',
      results: phenoToolEffectArrayJson1
    });

    expect(phenoResultsMock).toStrictEqual(phenoResultsMockFromJson);
  });
});
