import { Component, Input, OnChanges } from '@angular/core';
import { Validate } from 'class-validator';
import { SetNotEmpty } from '../utils/set.validators';
import { Store } from '@ngxs/store';
import { SetInheritanceTypes, InheritancetypesState } from './inheritancetypes.state';
import { StatefulComponent } from 'app/common/stateful-component';

@Component({
  selector: 'gpf-inheritancetypes',
  templateUrl: './inheritancetypes.component.html',
  styleUrls: ['./inheritancetypes.component.css'],
})
export class InheritancetypesComponent extends StatefulComponent implements OnChanges {

  @Input()
  inheritanceTypes: Set<string>;

  @Input()
  @Validate(SetNotEmpty, { message: 'select at least one' })
  selectedValues: Set<string> = new Set();

  constructor(protected store: Store) {
    super(store, InheritancetypesState, 'inheritanceTypes');
  }

  ngOnChanges() {
    this.store.selectOnce(state => state.inheritancetypesState).subscribe(state => {
      // handle selected values input and/or restore state
      if (state.inheritanceTypes.length) {
        this.selectedValues = new Set(state.inheritanceTypes);
      } else {
        this.store.dispatch(new SetInheritanceTypes(this.selectedValues));
      }
    });
  }

  updateInheritanceTypes(newValues: Set<string>): void {
    this.selectedValues = newValues;
    this.store.dispatch(new SetInheritanceTypes(newValues));
  }

  get inheritanceTypeDisplayNames() {
    return {
     'reference': 'Reference',
     'mendelian': 'Mendelian',
     'denovo': 'Denovo',
     'possible_denovo': 'Possible denovo',
     'omission': 'Omission',
     'possible_omission': 'Possible omission',
     'other': 'Other',
     'missing': 'Missing',
     'unknown': 'Unknown'
    };
  }
}
