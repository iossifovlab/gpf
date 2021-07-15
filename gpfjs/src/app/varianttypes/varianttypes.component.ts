import { Input, Component, OnChanges } from '@angular/core';
import { Validate } from 'class-validator';
import { SetNotEmpty } from '../utils/set.validators';
import { Store } from '@ngxs/store';
import { VarianttypesState, SetVariantTypes } from './varianttypes.state';
import { StatefulComponent } from '../common/stateful-component';

@Component({
  selector: 'gpf-varianttypes',
  templateUrl: './varianttypes.component.html',
  styleUrls: ['./varianttypes.component.css'],
})
export class VarianttypesComponent extends StatefulComponent implements OnChanges {

  @Input() variantTypes: Set<string> = new Set([]);
  @Input() @Validate(SetNotEmpty, {message: 'Select at least one'}) selectedVariantTypes: Set<string> = new Set();

  constructor(protected store: Store) {
    super(store, VarianttypesState, 'variantTypes');
  }

  ngOnChanges(): void {
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

  updateVariantTypes(newValues: Set<string>): void {
    this.selectedVariantTypes = newValues;
    this.store.dispatch(new SetVariantTypes(newValues));
  }
}
