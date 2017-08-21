export class MissenseScoresHistogramData {
  static fromJson(json: any): MissenseScoresHistogramData {
    return new MissenseScoresHistogramData(
      json['bars'],
      json['bins'],
      +json['min'],
      +json['max'],
    );
  }

  constructor(
    readonly bars: number[],
    readonly bins: number[],
    readonly min: number,
    readonly max: number,
  ) { }

}
