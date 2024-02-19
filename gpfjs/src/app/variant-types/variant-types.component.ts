import { Input, Component, OnChanges } from '@angular/core';
import { Validate } from 'class-validator';
import { SetNotEmpty } from '../utils/set.validators';
import { Store } from '@ngxs/store';
import { VarianttypesState, SetVariantTypes } from './variant-types.state';
import { StatefulComponent } from '../common/stateful-component';

@Component({
  selector: 'gpf-variant-types',
  templateUrl: './variant-types.component.html'
})
export class VariantTypesComponent extends StatefulComponent implements OnChanges {
  @Input() public variantTypes: Set<string> = new Set<string>([]);

  @Input()
  @Validate(SetNotEmpty, {message: 'Select at least one.'})
  public selectedVariantTypes: Set<string> = new Set();

  public constructor(protected store: Store) {
    super(store, VarianttypesState, 'variantTypes');
  }

  public ngOnChanges(): void {
    this.store.selectOnce(VarianttypesState).subscribe(state => {
      // handle selected values input and/or restore state
      if (state.variantTypes.length) {
        this.selectedVariantTypes = new Set(state.variantTypes);
      } else {
        // save the default selected variant types to the state
        this.store.dispatch(new SetVariantTypes(this.selectedVariantTypes));
      }
    });
  }

  public updateVariantTypes(newValues: Set<string>): void {
    this.selectedVariantTypes = newValues;
    this.store.dispatch(new SetVariantTypes(newValues));
  }
}
