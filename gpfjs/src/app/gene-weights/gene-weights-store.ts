import { GeneWeights } from './gene-weights';
import { IsNotEmpty, IsNumber, Min, Max, ValidateIf } from 'class-validator';
import { IsLessThanOrEqual } from '../utils/is-less-than-validator';
import { IsMoreThanOrEqual } from '../utils/is-more-than-validator';

export class GeneWeightsState {
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
};
