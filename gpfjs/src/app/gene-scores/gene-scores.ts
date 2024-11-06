import { IsNotEmpty, IsNumber, ValidateIf } from 'class-validator';
import { IsLessThanOrEqual } from '../utils/is-less-than-validator';
import { IsMoreThanOrEqual } from '../utils/is-more-than-validator';

export class GeneScores {
  public static fromJson(json: object): GeneScores {
    let histogram: NumberHistogram | CategoricalHistogram;
    /* eslint-disable @typescript-eslint/no-unsafe-member-access */
    /* eslint-disable @typescript-eslint/no-unsafe-assignment */
    if (json['histogram']['config']['type'] as string === 'number') {
      histogram = new NumberHistogram(
        json['histogram']['bars'] as number[],
        json['histogram']['bins'] as number[],
        json['large_values_desc'] as string,
        json['small_values_desc'] as string,
        json['histogram']['config']['view_range']['min'] as number,
        json['histogram']['config']['view_range']['max'] as number,
        json['histogram']['config']['x_log_scale"'] as boolean,
        json['histogram']['config']['y_log_scale"'] as boolean,
      );
    } else if (json['histogram']['config']['type'] as string === 'categorical') {
      const values: {name: string, value: number}[] = [];
      Object.keys(json['histogram']['values'] as object).forEach(key => {
        values.push({name: key, value: json['histogram']['values'][key]});
      });

      histogram = new CategoricalHistogram(
        values,
        json['histogram']['config']['value_order'] as string[],
        json['large_values_desc'] as string,
        json['small_values_desc'] as string,
        json['histogram']['config']['y_log_scale"'] as boolean,
        json['histogram']['config']['displayed_values_count'] as number,
        json['histogram']['config']['displayed_values_percent'] as number,
      );
    }
    /* eslint-enable */

    return new GeneScores(
      json['desc'] as string,
      json['help'] as string,
      json['score'] as string,
      histogram,
    );
  }

  public static fromJsonArray(jsonArray: Array<object>): Array<GeneScores> {
    return jsonArray.map((json) => GeneScores.fromJson(json));
  }


  public constructor(
    public readonly desc: string,
    public readonly help: string,
    public readonly score: string,
    public readonly histogram: NumberHistogram | CategoricalHistogram,
  ) {

  }
}

export class NumberHistogram {
  public constructor(
    public readonly bars: number[],
    public readonly bins: number[],
    public readonly largeValuesDesc: string,
    public readonly smallValuesDesc: string,
    public readonly rangeMin: number,
    public readonly rangeMax: number,
    public readonly logScaleX: boolean,
    public readonly logScaleY: boolean,
  ) {
    if (bins.length === (bars.length + 1)) {
      bars.push(0);
    }
  }
}

export class CategoricalHistogram {
  public constructor(
    public readonly values: {name: string, value: number}[],
    public readonly valueOrder: string[],
    public readonly largeValuesDesc: string,
    public readonly smallValuesDesc: string,
    public readonly logScaleY: boolean,
    public readonly displayedValuesCount: number = null,
    public readonly displayedValuesPercent: number = null,
  ) {

  }
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
