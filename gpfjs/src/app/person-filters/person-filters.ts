import { ValidateIf, ValidateNested, IsNumber, IsNotEmpty } from 'class-validator';
import { IsLessThanOrEqual } from '../utils/is-less-than-validator';
import { IsMoreThanOrEqual } from '../utils/is-more-than-validator';

export interface Selection {
  isEmpty(): boolean;
}

export class CategoricalSelection implements Selection {
  @IsNotEmpty()
  public selection: string[];

  public constructor(selection: string[] = []) {
    this.selection = selection;
  }

  public isEmpty(): boolean {
    return this.selection.length === 0;
  }
}

export class ContinuousSelection implements Selection {
  @ValidateIf(o => o.min !== null)
  @IsNumber()
  @IsLessThanOrEqual('max', {message: 'The range beginning must be lesser than the range end.'})
  @IsMoreThanOrEqual('domainMin', {message: 'The range beginning must be within the domain.'})
  public min: number;

  @ValidateIf(o => o.max !== null)
  @IsNumber()
  @IsMoreThanOrEqual('min', {message: 'The range end must be greater than the range start.'})
  @IsLessThanOrEqual('domainMax', {message: 'The range end must be within the domain.'})
  public max: number;

  public domainMin: number;
  public domainMax: number;

  public constructor(
    min: number, max: number, domainMin: number, domainMax: number,
  ) {
    this.min = min;
    this.max = max;
    this.domainMin = domainMin;
    this.domainMax = domainMax;
  }

  public isEmpty(): boolean {
    return this.min === this.max === null;
  }
}

export interface PersonFilterInterface {
  selection: Selection;
  source: string;
  id: string;
  sourceType: string;
  role: string;
  from: string;
}

export class PersonFilterState implements PersonFilterInterface {
  @ValidateNested()
  public selection: Selection;
  public source: string;

  public constructor(
    public readonly id: string,
    public readonly sourceType: string,
    public readonly role: string,
    source: string,
    public from: string,
    selection: Selection
  ) {
    this.selection = selection;
    this.source = source;
  }

  public isEmpty(): boolean {
    return this.source && this.source.length === 0;
  }
}

export class CategoricalFilterState extends PersonFilterState {
  public constructor(
    id: string,
    type: string,
    role: string,
    source: string,
    from: string,
    selection: CategoricalSelection = new CategoricalSelection(),
  ) {
    super(id, type, role, source, from, selection);
  }

  public isEmpty(): boolean {
    return this.selection.isEmpty() || super.isEmpty();
  }
}

export class ContinuousFilterState extends PersonFilterState {
  public constructor(
    id: string,
    type: string,
    role: string,
    source: string,
    from: string,
    selection: ContinuousSelection = new ContinuousSelection(null, null, null, null),
  ) {
    super(id, type, role, source, from, selection);
  }

  public isEmpty(): boolean {
    return !this.source;
  }
}
