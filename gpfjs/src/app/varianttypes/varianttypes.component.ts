import { Input, Component, OnInit, OnChanges } from '@angular/core';
import { validate, Validate } from 'class-validator';
import { SetNotEmpty } from '../utils/set.validators';
import { Select, Store } from '@ngxs/store';
import { VarianttypesState, VarianttypeModel, SetVariantTypes } from './varianttypes.state';
import { Observable } from 'rxjs';

@Component({
  selector: 'gpf-varianttypes',
  templateUrl: './varianttypes.component.html',
  styleUrls: ['./varianttypes.component.css'],
})
export class VarianttypesComponent implements OnInit, OnChanges {

  @Input() variantTypes: Set<string> = new Set([]);
  @Input() @Validate(SetNotEmpty, {message: 'select at least one'}) selectedVariantTypes: Set<string> = new Set([]);
  @Select(VarianttypesState) state$: Observable<VarianttypeModel>;
  errors: string[] = [];

  constructor(private store: Store) { }

  ngOnChanges(): void {
    if (this.selectedVariantTypes) {
      this.store.dispatch(new SetVariantTypes(this.selectedVariantTypes));
    }
  }

  ngOnInit() {
    this.selectedVariantTypes = new Set();
    this.store.selectOnce(state => state.varianttypesState).subscribe(state => {
      this.selectedVariantTypes = state.variantTypes;
    });

    this.state$.subscribe(state => {
      validate(this).then(errors => this.errors = errors.map(err => String(err)));
    });
  }

  updateVariantTypes(newValues: Set<string>): void {
    this.selectedVariantTypes = newValues;
    this.store.dispatch(new SetVariantTypes(newValues));
  }
}
