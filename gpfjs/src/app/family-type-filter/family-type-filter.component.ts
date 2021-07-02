import { Component, OnInit } from '@angular/core';
import { FamilyTypeFilterState, FamilyTypeFilterModel, SetFamilyTypeFilter } from './family-type-filter.state';
import { SetNotEmpty } from 'app/utils/set.validators';
import { Validate, validate } from 'class-validator';
import { Store, Select } from '@ngxs/store';
import { Observable } from 'rxjs';

@Component({
  selector: 'gpf-family-type-filter',
  templateUrl: './family-type-filter.component.html',
  styleUrls: ['./family-type-filter.component.css'],
})
export class FamilyTypeFilterComponent implements OnInit {

  allFamilyTypes: Set<string> = new Set(['trio', 'quad', 'multigenerational', 'simplex', 'multiplex']);
  @Validate(SetNotEmpty, {message: 'select at least one'}) selectedFamilyTypes: Set<string> = new Set();
  @Select(FamilyTypeFilterState) state$: Observable<FamilyTypeFilterModel>;
  errors: string[] = [];

  constructor(private store: Store) {}

  ngOnInit(): void {
    this.store.selectOnce(state => state.familyTypeFilterState).subscribe(state => {
      this.selectedFamilyTypes = new Set(state.familyTypes);
    });

    this.state$.subscribe(state => {
      validate(this).then(errors => this.errors = errors.map(err => String(err)));
    });
  }

  updateFamilyTypes(newValues: Set<string>): void {
    this.selectedFamilyTypes = newValues;
    this.store.dispatch(new SetFamilyTypeFilter(newValues));
  }
}
