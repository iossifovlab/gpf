import { Validate } from 'class-validator';
import { IsNumber, Min, Max } from 'class-validator';
import { IsLessThanOrEqual } from '../utils/is-less-than-validator';
import { IsMoreThanOrEqual } from '../utils/is-more-than-validator';

export class PhenoFilterState {
  constructor(
    readonly id: string,
    readonly measureType: string,
    readonly role: string,
    public measure: string,
  ) {}

  isEmpty() {
    return this.measure == null
        || this.measure.length === 0;
  }
}

export class CategoricalFilterState extends PhenoFilterState {
  selection = [];

  constructor(
    id: string,
    type: string,
    role: string,
    measure: string
  ) {
    super(id, type, role, measure);
  }

  isEmpty() {
    return this.selection.length === 0
        || super.isEmpty();
  }
};

export class ContinuousFilterState extends PhenoFilterState {
  @ValidateIf(o => o.mmin !== null)
  @IsNumber()
  @IsLessThanOrEqual('mmax')
  @IsMoreThanOrEqual('domainMin')
  mmin: number;

  @ValidateIf(o => o.mmax !== null)
  @IsNumber()
  @IsMoreThanOrEqual('mmin')
  @IsLessThanOrEqual('domainMax')
  mmax: number;

  domainMin: number;
  domainMax: number;

  constructor(
    id: string,
    role: string,
    measure: string
  ) {
    super(id, 'continuous', role, measure);
  }
};

export class PhenoFiltersState {
  phenoFilters: Array<PhenoFilterState> = [];
};
