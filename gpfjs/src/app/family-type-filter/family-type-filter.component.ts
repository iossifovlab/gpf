import { Component, OnInit } from '@angular/core';
import { selectFamilyTypeFilter, setFamilyTypeFilter } from './family-type-filter.state';
import { SetNotEmpty } from 'app/utils/set.validators';
import { Validate } from 'class-validator';
import { Store } from '@ngrx/store';
import { ComponentValidator } from 'app/common/component-validator';
import { take } from 'rxjs';

@Component({
  selector: 'gpf-family-type-filter',
  templateUrl: './family-type-filter.component.html',
  styleUrls: ['./family-type-filter.component.css'],
})
export class FamilyTypeFilterComponent extends ComponentValidator implements OnInit {
  public allFamilyTypes: Set<string> = new Set(['trio', 'quad', 'multigenerational', 'simplex', 'multiplex', 'other']);
  @Validate(SetNotEmpty, {message: 'Select at least one.'}) public selectedFamilyTypes: Set<string> = new Set();

  public constructor(protected store: Store) {
    super(store, 'familyTypeFilter', selectFamilyTypeFilter);
  }

  public ngOnInit(): void {
    super.ngOnInit();
    this.store.select(selectFamilyTypeFilter).pipe(take(1)).subscribe(familyTypesFilterState => {
      this.selectedFamilyTypes = new Set(familyTypesFilterState);
    });
  }

  public updateFamilyTypes(newValues: Set<string>): void {
    this.selectedFamilyTypes = newValues;
    this.store.dispatch(setFamilyTypeFilter({familyTypeFilter: [...newValues]}));
  }
}
