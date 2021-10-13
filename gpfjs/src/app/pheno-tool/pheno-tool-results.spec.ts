import { PhenoToolResult, PhenoToolResults, PhenoToolResultsPerEffect, PhenoToolResultsPerGender } from './pheno-tool-results';

describe('PhenoToolResult', () => {
  it('should create from json', () => {
    const phenoToolFromJson = PhenoToolResult.fromJson({
      count: 5,
      deviation: 3,
      mean: 4
    });
    expect(phenoToolFromJson).toEqual(new PhenoToolResult(5, 3, 4));
  });

  it('should get range start', () => {
    expect(new PhenoToolResult(5, 3, 4).rangeStart).toEqual(1);
  });

  it('should get range end', () => {
    expect(new PhenoToolResult(5, 3, 4).rangeEnd).toEqual(7);
  });
});

describe('PhenoToolResultsPerGender', () => {
  it('should create from json', () => {
    const phenoToolMockPositive = new PhenoToolResult(3, 8, 5);

    const phenoToolResultsPerGender = new PhenoToolResultsPerGender(
      phenoToolMockPositive, new PhenoToolResult(5, 3, 4), 5
    );

    const phenoToolResultsPerGenderFromJson = PhenoToolResultsPerGender.fromJson({
      positive: {
        count: 3,
        deviation: 8,
        mean: 5
      }, negative: {
        count: 5,
        deviation: 3,
        mean: 4
      }, pValue: 5
    });

    expect(phenoToolResultsPerGender).toEqual(phenoToolResultsPerGenderFromJson);
  });
});

describe('PhenoToolResultsPerEffect', () => {
  it('should create from json', () => {
    const phenoToolResultsPerEffect = new PhenoToolResultsPerEffect(
      'effectType1',
      new PhenoToolResultsPerGender(new PhenoToolResult(3, 8, 5), new PhenoToolResult(5, 3, 4), 5),
      new PhenoToolResultsPerGender(new PhenoToolResult(7, 9, 1), new PhenoToolResult(0, -1, 2), 7)
    );

    const phenoToolResultsPerEffectFromJson = PhenoToolResultsPerEffect.fromJson({
      effect: 'effectType1',
      maleResults: {
        positive: {
          count: 3,
          deviation: 8,
          mean: 5
        }, negative: {
          count: 5,
          deviation: 3,
          mean: 4
          }, pValue: 5
      }, femaleResults: {
        positive: {
          count: 7,
          deviation: 9,
          mean: 1
        }, negative: {
          count: 0,
          deviation: -1,
          mean: 2
        }, pValue: 7
      }
    });

    expect(phenoToolResultsPerEffect).toEqual(phenoToolResultsPerEffectFromJson);
  });

    it('should create from json array', () => {
      const phenoToolEffectArrayMock =
      [
        new PhenoToolResultsPerEffect(
          'effectType1',
          new PhenoToolResultsPerGender(new PhenoToolResult(3, 8, 5), new PhenoToolResult(5, 3, 4), 5),
          new PhenoToolResultsPerGender(new PhenoToolResult(7, 9, 1), new PhenoToolResult(0, -1, 2), 7)
        ),
        new PhenoToolResultsPerEffect(
          'effectType2',
          new PhenoToolResultsPerGender(new PhenoToolResult(7, 9, 2), new PhenoToolResult(3, 7, 2), 3),
          new PhenoToolResultsPerGender(new PhenoToolResult(1, 2, 3), new PhenoToolResult(9, 0, 4), 8)
        )
      ];

      const phenoToolEffectFromJsonArrayMock = PhenoToolResultsPerEffect.fromJsonArray([
        {
          effect: 'effectType1',
          maleResults: {
            positive: {
              count: 3,
              deviation: 8,
              mean: 5
            }, negative: {
              count: 5,
              deviation: 3,
              mean: 4
              }, pValue: 5
          }, femaleResults: {
            positive: {
              count: 7,
              deviation: 9,
              mean: 1
            }, negative: {
              count: 0,
              deviation: -1,
              mean: 2
            }, pValue: 7
          }
        }, {
          effect: 'effectType2',
          maleResults: {
            positive: {
              count: 7,
              deviation: 9,
              mean: 2
            }, negative: {
              count: 3,
              deviation: 7,
              mean: 2
              }, pValue: 3
          }, femaleResults: {
            positive: {
              count: 1,
              deviation: 2,
              mean: 3
            }, negative: {
              count: 9,
              deviation: 0,
              mean: 4
            }, pValue: 8
          }
        }
      ]);

      expect(phenoToolEffectArrayMock).toEqual(phenoToolEffectFromJsonArrayMock);
    });
});

describe('PhenoToolResults', () => {
  it('should create from json', () => {
    const phenoResultsMock = new PhenoToolResults(
      'desc1',
      [
        new PhenoToolResultsPerEffect(
          'effectType1',
          new PhenoToolResultsPerGender(new PhenoToolResult(3, 8, 5), new PhenoToolResult(5, 3, 4), 5),
          new PhenoToolResultsPerGender(new PhenoToolResult(7, 9, 1), new PhenoToolResult(0, -1, 2), 7)
        ),
        new PhenoToolResultsPerEffect(
          'effectType2',
          new PhenoToolResultsPerGender(new PhenoToolResult(7, 9, 2), new PhenoToolResult(3, 7, 2), 3),
          new PhenoToolResultsPerGender(new PhenoToolResult(1, 2, 3), new PhenoToolResult(9, 0, 4), 8)
        )
      ]
    );

    const phenoResultsMockFromJson = PhenoToolResults.fromJson({
      description: 'desc1',
      results: [
        {
          effect: 'effectType1',
          maleResults: {
            positive: {
              count: 3,
              deviation: 8,
              mean: 5
            }, negative: {
              count: 5,
              deviation: 3,
              mean: 4
              }, pValue: 5
          }, femaleResults: {
            positive: {
              count: 7,
              deviation: 9,
              mean: 1
            }, negative: {
              count: 0,
              deviation: -1,
              mean: 2
            }, pValue: 7
          }
        }, {
          effect: 'effectType2',
          maleResults: {
            positive: {
              count: 7,
              deviation: 9,
              mean: 2
            }, negative: {
              count: 3,
              deviation: 7,
              mean: 2
              }, pValue: 3
          }, femaleResults: {
            positive: {
              count: 1,
              deviation: 2,
              mean: 3
            }, negative: {
              count: 9,
              deviation: 0,
              mean: 4
            }, pValue: 8
          }
        }
      ]
    });

    expect(phenoResultsMock).toEqual(phenoResultsMockFromJson);
  });
});
