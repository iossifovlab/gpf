import { IsNotEmpty, IsNumber, ValidateIf } from 'class-validator';
import { IsLessThanOrEqual } from '../utils/is-less-than-validator';
import { IsMoreThanOrEqual } from '../utils/is-more-than-validator';

export class GeneWeights {
  readonly logScaleX: boolean;
  readonly logScaleY: boolean;
  static fromJson(json: any): GeneWeights {
    return new GeneWeights(
      json['bars'],
      json['weight'],
      json['bins'],
      json['desc'],
      json['range'],
      json['xscale'],
      json['yscale']
    );
  }

  static fromJsonArray(jsonArray: Array<Object>): Array<GeneWeights> {
    return jsonArray.map((json) => GeneWeights.fromJson(json));
  }


  constructor(
    readonly bars: number[],
    readonly weight: string,
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

export class GeneWeightsLocalState {
  @IsNotEmpty()
  weight: GeneWeights = null;

  @ValidateIf(o => o.rangeStart !== null)
  @IsNumber()
  @IsLessThanOrEqual('rangeEnd')
  @IsMoreThanOrEqual('domainMin')
  @IsLessThanOrEqual('domainMax')
  rangeStart = 0;

  @ValidateIf(o => o.rangeEnd !== null)
  @IsNumber()
  @IsMoreThanOrEqual('rangeStart')
  @IsMoreThanOrEqual('domainMin')
  @IsLessThanOrEqual('domainMax')
  rangeEnd = 0;

  domainMin = 0;
  domainMax = 0;
}
