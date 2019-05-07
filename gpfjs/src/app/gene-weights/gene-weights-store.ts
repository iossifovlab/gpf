import { GeneWeights } from './gene-weights';
import { IsNotEmpty, IsNumber, ValidateIf } from 'class-validator';
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

  changeDomain(weights: GeneWeights) {
    if (weights.domain != null) {
      this.domainMin = weights.domain[0];
      this.domainMax = weights.domain[1];
    } else {
      this.domainMin = weights.bins[0];
      this.domainMax =
        weights.bins[weights.bins.length - 1];
    }
  }
}
