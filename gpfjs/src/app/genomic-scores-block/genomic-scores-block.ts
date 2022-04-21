export class GenomicScores {
  public readonly logScaleX: boolean;
  public readonly logScaleY: boolean;
  public static fromJson(json): GenomicScores {
    return new GenomicScores(
      json['bars'],
      json['score'],
      json['bins'],
      json['range'],
      json['desc'],
      json['help'],
      json['xscale'],
      json['yscale']
    );
  }

  public static fromJsonArray(jsonArray: Array<object>): Array<GenomicScores> {
    return jsonArray.map((json) => GenomicScores.fromJson(json));
  }

  public constructor(
    public readonly bars: number[],
    public readonly score: string,
    public readonly bins: number[],
    public readonly domain: number[],
    public readonly desc: string,
    public readonly help: string,
    xScale: string,
    yScale: string
  ) {
    this.logScaleX = xScale === 'log';
    this.logScaleY = yScale === 'log';
  }
}
