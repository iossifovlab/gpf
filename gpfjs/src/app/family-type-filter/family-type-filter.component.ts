import { Component, OnInit } from '@angular/core';
import { FamilyTypeFilterState, SetFamilyTypeFilter } from './family-type-filter.state';
import { SetNotEmpty } from 'app/utils/set.validators';
import { Validate } from 'class-validator';
import { Store } from '@ngxs/store';
import { StatefulComponent } from 'app/common/stateful-component';

@Component({
  selector: 'gpf-family-type-filter',
  templateUrl: './family-type-filter.component.html',
  styleUrls: ['./family-type-filter.component.css'],
})
export class FamilyTypeFilterComponent extends StatefulComponent implements OnInit {
  public allFamilyTypes: Set<string> = new Set(['trio', 'quad', 'multigenerational', 'simplex', 'multiplex', 'other']);
  @Validate(SetNotEmpty, {message: 'Select at least one.'}) public selectedFamilyTypes: Set<string> = new Set();

  public constructor(protected store: Store) {
    super(store, FamilyTypeFilterState, 'familyTypeFilter');
  }

  public ngOnInit(): void {
    super.ngOnInit();
    this.store.selectOnce(state => state.familyTypeFilterState).subscribe(state => {
      this.selectedFamilyTypes = new Set(state.familyTypes);
    });
  }

  public updateFamilyTypes(newValues: Set<string>): void {
    this.selectedFamilyTypes = newValues;
    this.store.dispatch(new SetFamilyTypeFilter(newValues));
  }
}
