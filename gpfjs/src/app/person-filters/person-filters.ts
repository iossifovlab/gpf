import { ValidateIf, ValidateNested } from 'class-validator';
import { IsNumber } from 'class-validator';
import { IsLessThanOrEqual } from '../utils/is-less-than-validator';
import { IsMoreThanOrEqual } from '../utils/is-more-than-validator';

export interface Selection {
  isEmpty(): boolean;
}

export class CategoricalSelection implements Selection {
  constructor(public selection: string[] = []) {}

  isEmpty() {
    return this.selection.length === 0;
  }
}

export class ContinuousSelection implements Selection {
  @ValidateIf(o => o.min !== null)
  @IsNumber()
  @IsLessThanOrEqual('max')
  @IsMoreThanOrEqual('domainMin')
  min: number;

  @ValidateIf(o => o.max !== null)
  @IsNumber()
  @IsMoreThanOrEqual('min')
  @IsLessThanOrEqual('domainMax')
  max: number;

  domainMin: number;
  domainMax: number;

  constructor(
    min: number, max: number, domainMin: number, domainMax: number,
  ) {
    this.min = min;
    this.max = max;
    this.domainMin = domainMin;
    this.domainMax = domainMax;
  }

  isEmpty() {
    return this.min === this.max === null;
  }
}

export class PersonFilterState {

  @ValidateNested()
  selection: Selection

  constructor(
    readonly id: string,
    readonly sourceType: string,
    readonly role: string,
    public source: string,
    public from: string,
    selection: Selection
  ) {
    this.selection = selection;
  }

  isEmpty() {
    return this.source && this.source.length === 0;
  }
}

export class CategoricalFilterState extends PersonFilterState {

  constructor(
    id: string,
    type: string,
    role: string,
    source: string,
    from: string,
    selection: CategoricalSelection = new CategoricalSelection(),
  ) {
    super(id, type, role, source, from, selection);
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
    from: string,
    selection: ContinuousSelection = new ContinuousSelection(0,0,0,0),
  ) {
    super(id, type, role, source, from, selection);
  }
}
