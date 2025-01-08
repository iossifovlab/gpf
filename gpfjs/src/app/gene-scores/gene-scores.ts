import { IsNotEmpty, IsNumber, ValidateIf } from 'class-validator';
import { IsLessThanOrEqual } from '../utils/is-less-than-validator';
import { IsMoreThanOrEqual } from '../utils/is-more-than-validator';
import { GenomicScore } from 'app/genomic-scores-block/genomic-scores-block';

export class Partitions {
  public static fromJson(json: any): Partitions {
    return new Partitions(
      Number(json['left']['count']),
      Number(json['left']['percent']),
      Number(json['mid']['count']),
      Number(json['mid']['percent']),
      Number(json['right']['count']),
      Number(json['right']['percent']),
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
  public score: GenomicScore = null;

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
