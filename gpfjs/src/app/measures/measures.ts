export class ContinuousMeasure {
  public static fromJson(json: object): ContinuousMeasure {
    return new ContinuousMeasure(
      json['measure'] as string,
      json['min'] as number,
      json['max'] as number,
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
      json['bars'] as number[],
      json['measure'] as string,
      Number(json['min']),
      Number(json['max']),
      Number(json['step']),
      json['bins'] as number[],
      json['desc'] as string
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
