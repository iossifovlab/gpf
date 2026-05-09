import { ContinuousMeasure, HistogramData } from './measures';

describe('ContinuousMeasure', () => {
  it('should create from json', () => {
    const continuosMeasure = ContinuousMeasure.fromJson({
      measure: 'measure1',
      min: 1,
      max: 2
    });
    expect(continuosMeasure.name).toBe('measure1');
    expect(continuosMeasure.min).toBe(1);
    expect(continuosMeasure.max).toBe(2);
  });

  it('should correctly create from json with bad types', () => {
    const continuosMeasure = ContinuousMeasure.fromJson({
      measure: 1,
      min: 'abcd',
      max: 'abcd'
    });
    expect(continuosMeasure.name).toBe('1');
    expect(continuosMeasure.min).toBeNaN();
    expect(continuosMeasure.max).toBeNaN();
  });

  it('should create from json array', () => {
    const continuosMeasures = ContinuousMeasure.fromJsonArray([
      {
        measure: 'measure1',
        min: 1,
        max: 2
      },
      {
        measure: 'measure2',
        min: 3,
        max: 4
      }
    ]);
    expect(continuosMeasures[0].name).toBe('measure1');
    expect(continuosMeasures[0].min).toBe(1);
    expect(continuosMeasures[0].max).toBe(2);
    expect(continuosMeasures[1].name).toBe('measure2');
    expect(continuosMeasures[1].min).toBe(3);
    expect(continuosMeasures[1].max).toBe(4);
  });

  it('should return undefined when json array is invalid', () => {
    const continuosMeasures = ContinuousMeasure.fromJsonArray(null);
    expect(continuosMeasures).toBeUndefined();
  });
});

describe('HistogramData', () => {
  it('should create from json', () => {
    const histogramData = HistogramData.fromJson({
      bars: [1, 2],
      measure: 'measure1',
      min: 3,
      max: 4,
      step: 5,
      bins: [6, 7],
      desc: 'description1'
    });
    expect(histogramData.bars).toStrictEqual([1, 2]);
    expect(histogramData.measure).toBe('measure1');
    expect(histogramData.min).toBe(3);
    expect(histogramData.max).toBe(4);
    expect(histogramData.step).toBe(5);
    expect(histogramData.bins).toStrictEqual([6, 7]);
    expect(histogramData.desc).toBe('description1');
  });

  it('should correctly create from json with bad types', () => {
    const histogramData = HistogramData.fromJson({
      bars: ['1', '2'],
      measure: 123,
      min: 'abcd',
      max: 'abcd',
      step: 'abcd',
      bins: ['abcd', 'abcd'],
      desc: 123
    });
    expect(histogramData.bars).toStrictEqual([1, 2]);
    expect(histogramData.measure).toBe('123');
    expect(histogramData.min).toBeNaN();
    expect(histogramData.max).toBeNaN();
    expect(histogramData.step).toBeNaN();
    expect(histogramData.bins).toStrictEqual([NaN, NaN]);
    expect(histogramData.desc).toBe('123');
  });

  it('should create from json array', () => {
    const histogramDataArray = HistogramData.fromJsonArray([
      {
        bars: [1, 2],
        measure: 'measure1',
        min: 3,
        max: 4,
        step: 5,
        bins: [6, 7],
        desc: 'description1'
      },
      {
        bars: [8, 9],
        measure: 'measure2',
        min: 10,
        max: 11,
        step: 12,
        bins: [13, 14],
        desc: 'description2'
      },
    ]);
    expect(histogramDataArray[0].bars).toStrictEqual([1, 2]);
    expect(histogramDataArray[0].measure).toBe('measure1');
    expect(histogramDataArray[0].min).toBe(3);
    expect(histogramDataArray[0].max).toBe(4);
    expect(histogramDataArray[0].step).toBe(5);
    expect(histogramDataArray[0].bins).toStrictEqual([6, 7]);
    expect(histogramDataArray[0].desc).toBe('description1');
    expect(histogramDataArray[1].bars).toStrictEqual([8, 9]);
    expect(histogramDataArray[1].measure).toBe('measure2');
    expect(histogramDataArray[1].min).toBe(10);
    expect(histogramDataArray[1].max).toBe(11);
    expect(histogramDataArray[1].step).toBe(12);
    expect(histogramDataArray[1].bins).toStrictEqual([13, 14]);
    expect(histogramDataArray[1].desc).toBe('description2');
  });
});
