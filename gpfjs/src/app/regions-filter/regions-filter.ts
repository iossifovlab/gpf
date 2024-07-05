import { RegionsFilterValidator } from './regions-filter.validator';
import { Validate } from 'class-validator';

export class RegionsFilter {
  @Validate(RegionsFilterValidator)
  public regionsFilter = '';
  public genome = '';
}

