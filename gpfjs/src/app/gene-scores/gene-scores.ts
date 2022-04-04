import { IsNotEmpty, IsNumber, ValidateIf } from 'class-validator';
import { IsLessThanOrEqual } from '../utils/is-less-than-validator';
import { IsMoreThanOrEqual } from '../utils/is-more-than-validator';

export class GeneScores {
  readonly logScaleX: boolean;
  readonly logScaleY: boolean;
  static fromJson(json: any): GeneScores {
    return new GeneScores(
      json['bars'],
      json['score'],
      json['bins'],
      json['desc'],
      json['range'],
      json['xscale'],
      json['yscale']
    );
  }

  static fromJsonArray(jsonArray: Array<Object>): Array<GeneScores> {
    return jsonArray.map((json) => GeneScores.fromJson(json));
  }


  constructor(
    readonly bars: number[],
    readonly score: string,
    readonly bins: number[],
    readonly desc: string,
    readonly domain: number[],
    xScale: string,
    yScale: string
  ) {
    if (bins.length === (bars.length + 1)) {
      bars.push(0);
    }
    this.logScaleX = xScale === 'log';
    this.logScaleY = yScale === 'log';

  }

}

export class Partitions {
  static fromJson(json: any): Partitions {
    return new Partitions(
      +json['left']['count'],
      +json['left']['percent'],
      +json['mid']['count'],
      +json['mid']['percent'],
      +json['right']['count'],
      +json['right']['percent'],
    );
  }

  constructor(
    readonly leftCount: number,
    readonly leftPercent: number,
    readonly midCount: number,
    readonly midPercent: number,
    readonly rightCount: number,
    readonly rightPercent: number,
  ) { }

}

export class GeneScoresLocalState {
  @IsNotEmpty()
  score: GeneScores = null;

  @ValidateIf(o => o.rangeStart !== null)
  @IsNumber()
  @IsLessThanOrEqual('rangeEnd', {message: 'The range beginning must be lesser than the range end.'})
  @IsMoreThanOrEqual('domainMin', {message: 'The range beginning must be within the domain.'})
  @IsLessThanOrEqual('domainMax', {message: 'The range beginning must be within the domain.'})
  rangeStart = 0;

  @ValidateIf(o => o.rangeEnd !== null)
  @IsNumber()
  @IsMoreThanOrEqual('rangeStart', {message: 'The range end must be greater than the range start.'})
  @IsMoreThanOrEqual('domainMin', {message: 'The range end must be within the domain.'})
  @IsLessThanOrEqual('domainMax', {message: 'The range end must be within the domain.'})
  rangeEnd = 0;

  domainMin = 0;
  domainMax = 0;
}
