import { ValidateIf } from 'class-validator';
import { IsNumber } from 'class-validator';
import { IsLessThanOrEqual } from '../utils/is-less-than-validator';
import { IsMoreThanOrEqual } from '../utils/is-more-than-validator';

export interface Selection {
  isEmpty(): boolean;
}

export class CategoricalSelection implements Selection {
  selection: string[] = [];

  isEmpty() {
    return this.selection.length === 0;
  }
}

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

export class PersonFilterState {
  constructor(
    readonly id: string,
    readonly sourceType: string,
    readonly role: string,
    public source: string,
    public from: string,
    public selection: Selection
  ) {}

  isEmpty() {
    return this.source == null || this.source.length === 0;
  }
}

export class CategoricalFilterState extends PersonFilterState {

  constructor(
    id: string,
    type: string,
    role: string,
    source: string,
    from: string
  ) {
    super(id, type, role, source, from, new CategoricalSelection());
  }

  isEmpty() {
    return this.selection.isEmpty() || super.isEmpty();
  }
}

export class ContinuousFilterState extends PersonFilterState {

  constructor(
    id: string,
    type: string,
    role: string,
    source: string,
    from: string
  ) {
    super(id, type, role, source, from, new ContinuousSelection());
  }
}
