import { Component, Input, OnInit, OnChanges, forwardRef } from '@angular/core';
import { Validate, validate } from 'class-validator';
import { SetNotEmpty } from '../utils/set.validators';
import { Observable } from 'rxjs';
import { Store, Select } from '@ngxs/store';
import { SetInheritanceTypes, InheritancetypesModel, InheritancetypesState } from './inheritancetypes.state';

@Component({
  selector: 'gpf-inheritancetypes',
  templateUrl: './inheritancetypes.component.html',
  styleUrls: ['./inheritancetypes.component.css'],
})
export class InheritancetypesComponent implements OnInit, OnChanges {

  @Input()
  inheritanceTypes: Set<string>;

  @Input()
  @Validate(SetNotEmpty, { message: 'select at least one' })
  selectedValues: Set<string> = new Set();

  @Select(InheritancetypesState) state$: Observable<InheritancetypesModel>;
  errors: Array<string> = [];

  constructor(private store: Store) { }

  ngOnInit() {
    this.store.selectOnce(state => state.inheritancetypesState).subscribe(state => {
      // restore state
      this.selectedValues = state.inheritanceTypes;
    });

    this.state$.subscribe(state => {
      // validate for errors
      validate(this.inheritanceTypes).then(errors => this.errors = errors.map(err => String(err)));
    });
  }

  ngOnChanges() {
    if (this.selectedValues) {
      this.store.dispatch(new SetInheritanceTypes(this.selectedValues));
    }
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
