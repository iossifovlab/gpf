import { ContinuousMeasure, HistogramData } from "./measures";

describe('ContinuousMeasure', () => {
  it('should create from json', () => {
    const continuosMeasure = ContinuousMeasure.fromJson({
      measure: 'measure1',
      min: 1,
      max: 2
    });
    expect(continuosMeasure.name).toEqual('measure1');
    expect(continuosMeasure.min).toEqual(1);
    expect(continuosMeasure.max).toEqual(2);
  });

  it('should correctly create from json with bad types', () => {
    const continuosMeasure = ContinuousMeasure.fromJson({
      measure: 1,
      min: 'abcd',
      max: 'abcd'
    });
    expect(continuosMeasure.name).toEqual('1');
    expect(continuosMeasure.min).toEqual(NaN);
    expect(continuosMeasure.max).toEqual(NaN);
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
    expect(continuosMeasures[0].name).toEqual('measure1');
    expect(continuosMeasures[0].min).toEqual(1);
    expect(continuosMeasures[0].max).toEqual(2);
    expect(continuosMeasures[1].name).toEqual('measure2');
    expect(continuosMeasures[1].min).toEqual(3);
    expect(continuosMeasures[1].max).toEqual(4);
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
    expect(histogramData.bars).toEqual([1, 2]);
    expect(histogramData.measure).toEqual('measure1');
    expect(histogramData.min).toEqual(3);
    expect(histogramData.max).toEqual(4);
    expect(histogramData.step).toEqual(5);
    expect(histogramData.bins).toEqual([6, 7]);
    expect(histogramData.desc).toEqual('description1');
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
    expect(histogramData.bars).toEqual([1, 2]);
    expect(histogramData.measure).toEqual('123');
    expect(histogramData.min).toEqual(NaN);
    expect(histogramData.max).toEqual(NaN);
    expect(histogramData.step).toEqual(NaN);
    expect(histogramData.bins).toEqual([NaN, NaN]);
    expect(histogramData.desc).toEqual('123');
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
    expect(histogramDataArray[0].bars).toEqual([1, 2]);
    expect(histogramDataArray[0].measure).toEqual('measure1');
    expect(histogramDataArray[0].min).toEqual(3);
    expect(histogramDataArray[0].max).toEqual(4);
    expect(histogramDataArray[0].step).toEqual(5);
    expect(histogramDataArray[0].bins).toEqual([6, 7]);
    expect(histogramDataArray[0].desc).toEqual('description1');
    expect(histogramDataArray[1].bars).toEqual([8, 9]);
    expect(histogramDataArray[1].measure).toEqual('measure2');
    expect(histogramDataArray[1].min).toEqual(10);
    expect(histogramDataArray[1].max).toEqual(11);
    expect(histogramDataArray[1].step).toEqual(12);
    expect(histogramDataArray[1].bins).toEqual([13, 14]);
    expect(histogramDataArray[1].desc).toEqual('description2');
  });
});
