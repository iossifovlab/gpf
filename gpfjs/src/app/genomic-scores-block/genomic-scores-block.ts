export class GenomicScores {
  readonly logScaleX: boolean;
  readonly logScaleY: boolean;
  static fromJson(json: any): GenomicScores {
    return new GenomicScores(
      json['bars'],
      json['score'],
      json['bins'],
      json['desc'],
      json['xscale'],
      json['yscale']
    );
  }

  static fromJsonArray(jsonArray: Array<Object>): Array<GenomicScores> {
    return jsonArray.map((json) => GenomicScores.fromJson(json));
  }

  constructor(
    readonly bars: number[],
    readonly score: string,
    readonly bins: number[],
    readonly desc: string,
    xScale: string,
    yScale:  string
  ) {
    this.logScaleX = xScale === 'log';
    this.logScaleY = yScale === 'log';
  }
}