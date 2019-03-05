import { Validate, ValidateIf } from 'class-validator';
import { IsNumber, Min, Max } from 'class-validator';
import { IsLessThanOrEqual } from '../utils/is-less-than-validator';
import { IsMoreThanOrEqual } from '../utils/is-more-than-validator';

export interface Selection{
  isEmpty(): boolean;
}

export class PhenoFilterState {
  constructor(
    readonly id: string,
    readonly measureType: string,
    readonly role: string,
    public measure: string,
    public selection: Selection
  ) {}

  isEmpty() {
    return this.measure == null
        || this.measure.length === 0;
  }
}

export class CategoricalSelection implements Selection {
  selection: string[] = [];

  isEmpty() {
    return this.selection.length === 0;
  }
}

export class CategoricalFilterState extends PhenoFilterState {

  constructor(
    id: string,
    // name: string,
    type: string,
    role: string,
    measure: string
  ) {
    super(id, type, role, measure, new CategoricalSelection());
  }

  isEmpty() {
    return this.selection.isEmpty() || super.isEmpty();
  }
};

export class ContinuousSelection implements Selection {
  @ValidateIf(o => o.mmin !== null)
  @IsNumber()
  @IsLessThanOrEqual('mmax')
  @IsMoreThanOrEqual('domainMin')
  min: number;

  @ValidateIf(o => o.mmax !== null)
  @IsNumber()
  @IsMoreThanOrEqual('mmin')
  @IsLessThanOrEqual('domainMax')
  max: number;

  domainMin: number;
  domainMax: number;

  isEmpty() {
    return this.min === this.max === null;
  }
}

export class ContinuousFilterState extends PhenoFilterState {

  constructor(
    id: string,
    type: string,
    role: string,
    measure: string
  ) {
    super(id, type, role, measure, new ContinuousSelection());
  }
};

export class PhenoFiltersState {
  phenoFilters: Array<PhenoFilterState> = [];
};
