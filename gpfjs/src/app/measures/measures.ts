export class ContinuousMeasure {
  static fromJson(json: any): ContinuousMeasure {
    return new ContinuousMeasure(
      json['measure'],
      json['min'],
      json['max'],
    );
  }

  static fromJsonArray(jsonArray: Array<Object>): Array<ContinuousMeasure> {
    if (!jsonArray) {
      return undefined;
    }
    return jsonArray.map((json) => ContinuousMeasure.fromJson(json));
  }

  constructor(
    readonly name: string,
    readonly min: number,
    readonly max: number
  ) {}
}


export class HistogramData {
  static fromJson(json: any): HistogramData {
    return new HistogramData(
      json['bars'],
      json['measure'],
      +json['min'],
      +json['max'],
      +json['step'],
      json['bins'],
      json['desc']
    );
  }

  static fromJsonArray(jsonArray: Array<Object>): Array<HistogramData> {
    return jsonArray.map((json) => HistogramData.fromJson(json));
  }

  constructor(
    readonly bars: number[],
    readonly measure: string,
    readonly min: number,
    readonly max: number,
    readonly step: number,
    readonly bins: number[],
    readonly desc: string,
  ) { }

}
