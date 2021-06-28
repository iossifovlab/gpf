import { Component, Input, OnInit, OnChanges, forwardRef } from '@angular/core';
import { InheritanceTypes, inheritanceTypeDisplayNames  } from './inheritancetypes';
import { validate } from 'class-validator';
import { Observable } from 'rxjs';
import { Store, Select } from '@ngxs/store';
import { AddInheritanceType, RemoveInheritanceType, InheritancetypesModel, InheritancetypesState } from './inheritancetypes.state';

@Component({
  selector: 'gpf-inheritancetypes',
  templateUrl: './inheritancetypes.component.html',
  styleUrls: ['./inheritancetypes.component.css'],
})
export class InheritancetypesComponent implements OnInit, OnChanges {

  @Input() inheritanceTypeFilter: Array<string>;
  @Input() selectedInheritanceTypeFilterValues: Array<string>;
  @Select(InheritancetypesState) state$: Observable<InheritancetypesModel>;
  inheritanceTypes: InheritanceTypes;
  errors: Array<string> = [];

  constructor(
    private store: Store
  ) {
    this.inheritanceTypes = new InheritanceTypes([]);
  }

  ngOnInit() {
    this.store.selectOnce(state => state.inheritancetypesState).subscribe(state => {
      // restore state
      this.inheritanceTypes.selected.clear();
      for (const inh of state.inheritanceTypes) {
        this.addInheritanceType(inh);
      }
    });

    this.state$.subscribe(state => {
      // validate for errors
      validate(this.inheritanceTypes).then(errors => this.errors = errors.map(err => String(err)));
    });
  }

  ngOnChanges() {
    this.inheritanceTypeFilter.map(inh => this.inheritanceTypes.available.add(inh));
    this.selectedInheritanceTypeFilterValues.map(inh => this.addInheritanceType(inh));
  }

  addInheritanceType(inheritanceType: string) {
    this.inheritanceTypes.selected.add(inheritanceType);
    this.store.dispatch(new AddInheritanceType(inheritanceType));
  }

  removeInheritanceType(inheritanceType: string) {
    this.inheritanceTypes.selected.delete(inheritanceType);
    this.store.dispatch(new RemoveInheritanceType(inheritanceType));
  }

  toggleInheritanceType(inheritanceType: string) {
    if (this.inheritanceTypes.selected.has(inheritanceType)) {
      this.removeInheritanceType(inheritanceType);
    } else {
      this.addInheritanceType(inheritanceType);
    }
  }

  getDisplayName(inheritanceType: string) {
    return inheritanceTypeDisplayNames[inheritanceType] || inheritanceType;
  }

  selectAll() {
    for (const inh of this.inheritanceTypes.available) {
      this.addInheritanceType(inh);
    }
  }

  selectNone() {
    for (const inh of this.inheritanceTypes.available) {
      this.removeInheritanceType(inh);
    }
  }
}
