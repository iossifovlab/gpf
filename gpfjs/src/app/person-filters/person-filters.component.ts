import { Component, OnChanges, Input, OnInit } from '@angular/core';
import { Dataset, PersonFilter } from '../datasets/datasets';
import {
  CategoricalFilterState,
  CategoricalSelection,
  ContinuousFilterState,
  PersonFilterState,
} from './person-filters';
import { Store } from '@ngrx/store';
import { PersonAndFamilyFilters, selectPersonFilters, setFamilyFilters, setPersonFilters } from './person-filters.state';
import { IsNotEmpty, ValidateNested } from 'class-validator';
import { StatefulComponent } from 'app/common/stateful-component';
import { cloneDeep } from 'lodash';
import { take } from 'rxjs';

@Component({
  selector: 'gpf-person-filters',
  templateUrl: './person-filters.component.html',
  styleUrls: ['./person-filters.component.css'],
})
export class PersonFiltersComponent extends StatefulComponent implements OnInit {
  @Input() public dataset: Dataset;
  @Input() public isFamilyFilters: boolean;

  public selectedDatasetId: string;
  public categoricalFilters: PersonFilterState[] = [];
  public continuousFilters: PersonFilterState[] = [];

  @IsNotEmpty({message: 'Select at least one continuous filter.'})
  public selected = false;

  public constructor(protected store: Store) {
    super(store, 'personFilters', selectPersonFilters);
  }

  public ngOnInit(): void {
    this.selectedDatasetId = this.dataset.id;

    this.store.select(selectPersonFilters).pipe(take(1)).subscribe((state: PersonAndFamilyFilters) => {
      const clonedState = cloneDeep(state);
      // set default state
      if (!state.familyFilters || !state.personFilters) {
        const defaultFilters = this.isFamilyFilters ?
          this.dataset.genotypeBrowserConfig.familyFilters : this.dataset.genotypeBrowserConfig.personFilters;

        for (const defaultFilter of defaultFilters) {
          if (defaultFilter.sourceType === 'continuous') {
            this.continuousFilters.push(
              new ContinuousFilterState(
                defaultFilter.name,
                defaultFilter.sourceType,
                defaultFilter.role,
                defaultFilter.source,
                defaultFilter.from,
              )
            );
          } else if (defaultFilter.sourceType === 'categorical') {
            this.categoricalFilters.push(
              new CategoricalFilterState(
                defaultFilter.name,
                defaultFilter.sourceType,
                defaultFilter.role,
                defaultFilter.source,
                defaultFilter.from,
              )
            );
          } else {
            console.error(`Unexpected filter type:${defaultFilter.sourceType} in ${defaultFilter.name}`);
          }
        }
        return;
      }

      const filters: PersonFilterState[] = this.isFamilyFilters ? clonedState.familyFilters : clonedState.personFilters;
      for (const filter of filters) {
        if (filter.sourceType === 'continuous') {
          this.continuousFilters.push(filter);
        } else if (filter.sourceType === 'categorical') {
          this.categoricalFilters.push(filter);
        } else {
          console.error(`Unexpected filter type:${filter.sourceType} in ${filter.id}`);
        }
      }
    });
  }
}
