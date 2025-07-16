import { Input, Component, OnInit } from '@angular/core';
import { Validate } from 'class-validator';
import { SetNotEmpty } from '../utils/set.validators';
import { Store } from '@ngrx/store';
import { selectVariantTypes, setVariantTypes } from './variant-types.state';
import { take } from 'rxjs';
import { resetErrors, setErrors } from 'app/common/errors.state';
import { cloneDeep } from 'lodash';

@Component({
    selector: 'gpf-variant-types',
    templateUrl: './variant-types.component.html',
    styleUrls: ['./variant-types.css'],
    standalone: false
})
export class VariantTypesComponent implements OnInit {
  @Input() public variantTypes: Set<string> = new Set<string>([]);

  @Input()
  @Validate(SetNotEmpty, {message: 'Select at least one.'})
  public selectedVariantTypes: Set<string> = new Set();
  public errors: string[] = [];

  public constructor(protected store: Store) {}

  public ngOnInit(): void {
    this.store.select(selectVariantTypes).pipe(take(1)).subscribe(variantTypesState => {
      this.selectedVariantTypes = new Set(variantTypesState);
      this.validateState();
    });
  }

  public updateVariantTypes(newValues: Set<string>): void {
    this.selectedVariantTypes = newValues;
    this.validateState();
    this.store.dispatch(setVariantTypes({ variantTypes: [...newValues] }));
  }

  private validateState(): void {
    this.errors = [];
    if (!this.selectedVariantTypes.size) {
      this.errors.push('Select at least one.');
    }

    if (this.errors.length) {
      this.store.dispatch(setErrors({
        errors: {
          componentId: 'variantTypes', errors: cloneDeep(this.errors)
        }
      }));
    } else {
      this.store.dispatch(resetErrors({componentId: 'variantTypes'}));
    }
  }
}
