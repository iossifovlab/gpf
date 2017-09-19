export class GenomicScoresHistogramData {
  static fromJson(json: any): GenomicScoresHistogramData {
    return new GenomicScoresHistogramData(
      json['id'],
      json['bars'],
      json['bins'],
      +json['min'],
      +json['max'],
    );
  }

  constructor(
    readonly metric: string,
    readonly bars: number[],
    readonly bins: number[],
    readonly min: number,
    readonly max: number,
  ) { }

}
