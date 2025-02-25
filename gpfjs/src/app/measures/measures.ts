import { NumberHistogram, CategoricalHistogram } from 'app/utils/histogram-types';

export class ContinuousMeasure {
  public static fromJson(json: object): ContinuousMeasure {
    return new ContinuousMeasure(
      String(json['measure']),
      Number(json['min']),
      Number(json['max']),
    );
  }

  public static fromJsonArray(jsonArray: object[]): Array<ContinuousMeasure> {
    if (!jsonArray) {
      return undefined;
    }
    return jsonArray.map((json) => ContinuousMeasure.fromJson(json));
  }

  public constructor(
    public readonly name: string,
    public readonly min: number,
    public readonly max: number
  ) {}
}


export class HistogramData {
  public static fromJson(json: object): HistogramData {
    return new HistogramData(
      (json['bars'] as number[]).map(bar => Number(bar)),
      String(json['measure']),
      Number(json['min']),
      Number(json['max']),
      Number(json['step']),
      (json['bins'] as number[]).map(bin => Number(bin)),
      String(json['desc'])
    );
  }

  public static fromJsonArray(jsonArray: Array<object>): Array<HistogramData> {
    return jsonArray.map((json) => HistogramData.fromJson(json));
  }

  public constructor(
    public readonly bars: number[],
    public readonly measure: string,
    public readonly min: number,
    public readonly max: number,
    public readonly step: number,
    public readonly bins: number[],
    public readonly desc: string,
  ) { }
}


export class MeasureHistogram {
  public static fromJson(json: object): MeasureHistogram {
    let histogram: NumberHistogram | CategoricalHistogram;
    /* eslint-disable @typescript-eslint/no-unsafe-member-access */
    /* eslint-disable @typescript-eslint/no-unsafe-assignment */
    if (json['histogram']['config']['type'] as string === 'number') {
      histogram = new NumberHistogram(
        json['histogram']['bars'] as number[],
        json['histogram']['bins'] as number[],
        null,
        null,
        json['histogram']['config']['view_range']['min'] as number,
        json['histogram']['config']['view_range']['max'] as number,
        json['histogram']['config']['x_log_scale'] as boolean,
        json['histogram']['config']['y_log_scale'] as boolean,
      );
    } else if (json['histogram']['config']['type'] as string === 'categorical') {
      const values: {name: string, value: number}[] = [];
      Object.keys(json['histogram']['values'] as object).forEach(key => {
        values.push({name: key, value: json['histogram']['values'][key]});
      });

      let valueOrder: string[] = [];
      if (json['histogram']['config']['value_order']?.length > 0) {
        valueOrder = json['histogram']['config']['value_order'];
      }

      histogram = new CategoricalHistogram(
        values,
        valueOrder,
        null,
        null,
        json['histogram']['config']['y_log_scale'] as boolean,
        json['histogram']['config']['label_rotation'] as number,
        json['histogram']['config']['displayed_values_count'] as number,
        json['histogram']['config']['displayed_values_percent'] as number,
      );
    }

    return new MeasureHistogram(
      String(json['measure']),
      histogram
    );
  }

  public static fromJsonArray(jsonArray: Array<object>): Array<MeasureHistogram> {
    return jsonArray.map((json) => MeasureHistogram.fromJson(json));
  }

  public constructor(
    public readonly measure: string,
    public readonly histogram: NumberHistogram | CategoricalHistogram
  ) { }
}
