export class GenomicScores {
  public readonly logScaleX: boolean;
  public readonly logScaleY: boolean;
  public static fromJson(json: object): GenomicScores {
    return new GenomicScores(
      json['bars'] as number[],
      json['bins'] as number[],
      json['desc'] as string,
      json['help'] as string,
      json['large_values_desc'] as string,
      json['small_values_desc'] as string,
      json['score'] as string,
      json['xscale'] as string,
      json['yscale'] as string
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
