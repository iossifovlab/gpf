import { IsNotEmpty, IsNumber, ValidateIf } from 'class-validator';
import { IsLessThanOrEqual } from '../utils/is-less-than-validator';
import { IsMoreThanOrEqual } from '../utils/is-more-than-validator';

export class GeneScores {
  public readonly logScaleX: boolean;
  public readonly logScaleY: boolean;
  public static fromJson(json: object): GeneScores {
    return new GeneScores(
      json['bars'] as number[],
      json['bins'] as number[],
      json['desc'] as string,
      json['help'] as string,
      json['large_values_desc'] as string,
      json['small_values_desc'] as string,
      json['score'] as string,
      json['range'] as number[],
      json['xscale'] as string,
      json['yscale'] as string
    );
  }

  public static fromJsonArray(jsonArray: Array<object>): Array<GeneScores> {
    return jsonArray.map((json) => GeneScores.fromJson(json));
  }


  public constructor(
    public readonly bars: number[],
    public readonly bins: number[],
    public readonly desc: string,
    public readonly help: string,
    public readonly largeValuesDesc: string,
    public readonly smallValuesDesc: string,
    public readonly score: string,
    public readonly domain: number[],
    private xScale: string,
    private yScale: string,

  ) {
    if (bins.length === (bars.length + 1)) {
      bars.push(0);
    }
    this.logScaleX = xScale === 'log';
    this.logScaleY = yScale === 'log';
  }
}

export class Partitions {
  public static fromJson(json: any): Partitions {
    return new Partitions(
      +json['left']['count'],
      +json['left']['percent'],
      +json['mid']['count'],
      +json['mid']['percent'],
      +json['right']['count'],
      +json['right']['percent'],
    );
  }

  public constructor(
    public readonly leftCount: number,
    private readonly leftPercent: number,
    public readonly midCount: number,
    private readonly midPercent: number,
    public readonly rightCount: number,
    private readonly rightPercent: number,
  ) { }
}

export class GeneScoresLocalState {
  @IsNotEmpty()
  public score: GeneScores = null;

  @ValidateIf(o => o.rangeStart !== null)
  @IsNumber()
  @IsLessThanOrEqual('rangeEnd', {message: 'The range beginning must be lesser than the range end.'})
  @IsMoreThanOrEqual('domainMin', {message: 'The range beginning must be within the domain.'})
  @IsLessThanOrEqual('domainMax', {message: 'The range beginning must be within the domain.'})
  public rangeStart = 0;

  @ValidateIf(o => o.rangeEnd !== null)
  @IsNumber()
  @IsMoreThanOrEqual('rangeStart', {message: 'The range end must be greater than the range start.'})
  @IsMoreThanOrEqual('domainMin', {message: 'The range end must be within the domain.'})
  @IsLessThanOrEqual('domainMax', {message: 'The range end must be within the domain.'})
  public rangeEnd = 0;

  public domainMin = 0;
  public domainMax = 0;
}
