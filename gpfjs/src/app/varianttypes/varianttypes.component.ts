import { Input, Component, OnInit, OnChanges } from '@angular/core';
import { validate, Validate } from 'class-validator';
import { SetNotEmpty } from '../utils/set.validators';
import { Select, Store } from '@ngxs/store';
import { VarianttypesState, VarianttypeModel, AddVariantType, RemoveVariantType } from './varianttypes.state';
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
      this.selectedVariantTypes.forEach(variantType => {
        this.variantTypesCheckValue(variantType, false);
      });
    }
  }

  ngOnInit() {
    this.selectedVariantTypes = new Set();
    this.store.selectOnce(state => state.varianttypesState).subscribe(state => {
      for (const variantType of state.variantTypes) {
        this.variantTypesCheckValue(variantType, false);
      }
    });

    this.state$.subscribe(() => {
      validate(this).then(errors => this.errors = errors.map(err => String(err)));
    });
  }

  addVariantType(variantType: string): void {
    this.selectedVariantTypes.add(variantType);
    this.store.dispatch(new AddVariantType(variantType));
  }

  removeVariantType(variantType: string): void {
    this.selectedVariantTypes.delete(variantType);
    this.store.dispatch(new RemoveVariantType(variantType));
  }

  selectAll(): void {
    for (const variantType of this.variantTypes) {
      this.addVariantType(variantType);
    }
  }

  selectNone(): void {
    for (const variantType of this.variantTypes) {
      this.removeVariantType(variantType);
    }
  }

  variantTypesCheckValue(variantType: string, value: boolean): void {
    if (!this.variantTypes.has(variantType)) {
      return;
    }

    if (!value) {
      this.addVariantType(variantType);
    } else {
      this.removeVariantType(variantType);
    }
  }
}
