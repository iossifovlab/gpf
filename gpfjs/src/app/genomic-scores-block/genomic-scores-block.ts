export class GenomicScores {
  public readonly logScaleX: boolean;
  public readonly logScaleY: boolean;
  public static fromJson(json): GenomicScores {
    return new GenomicScores(
      json['bars'],
      json['bins'],
      json['desc'],
      json['help'],
      json['large_values_desc'],
      json['small_values_desc'],
      json['score'],
      json['xscale'],
      json['yscale']
    );
  }

  public static fromJsonArray(jsonArray: Array<object>): Array<GenomicScores> {
    return jsonArray.map((json) => GenomicScores.fromJson(json));
  }

  public constructor(
    public readonly bars: number[],
    public readonly bins: number[],
    public readonly desc: string,
    public readonly help: string,
    public readonly largeValuesDesc: string,
    public readonly smallValuesDesc: string,
    public readonly score: string,
    xScale: string,
    yScale: string
  ) {
    this.logScaleX = xScale === 'log';
    this.logScaleY = yScale === 'log';
  }
}
