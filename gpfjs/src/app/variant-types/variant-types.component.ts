import { Input, Component, OnChanges } from '@angular/core';
import { Validate } from 'class-validator';
import { SetNotEmpty } from '../utils/set.validators';
import { Store } from '@ngrx/store';
import { StatefulComponentNgRx } from 'app/common/stateful-component_ngrx';
import { selectVariantTypes, setVariantTypes } from './variant-types.state';
import { take } from 'rxjs';

@Component({
  selector: 'gpf-variant-types',
  templateUrl: './variant-types.component.html'
})
export class VariantTypesComponent extends StatefulComponentNgRx implements OnChanges {
  @Input() public variantTypes: Set<string> = new Set<string>([]);

  @Input()
  @Validate(SetNotEmpty, {message: 'Select at least one.'})
  public selectedVariantTypes: Set<string> = new Set();

  public constructor(protected store: Store) {
    super(store, 'variantTypes', selectVariantTypes);
  }

  public ngOnChanges(): void {
    this.store.select(selectVariantTypes).pipe(take(1)).subscribe(variantTypesState => {
      // handle selected values input and/or restore state
      if (variantTypesState.length) {
        this.selectedVariantTypes = new Set(variantTypesState);
      } else {
        // save the default selected variant types to the state
        this.store.dispatch(setVariantTypes({variantTypes: [...this.selectedVariantTypes]}));
      }
    });
  }

  public updateVariantTypes(newValues: Set<string>): void {
    this.selectedVariantTypes = newValues;
    this.store.dispatch(setVariantTypes({variantTypes: [...newValues]}));
  }
}
