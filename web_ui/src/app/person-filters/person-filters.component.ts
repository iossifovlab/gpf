import { Component, Input, OnInit, inject, OnDestroy } from '@angular/core';
import { Dataset } from '../datasets/datasets';
import {
  CategoricalFilterState,
  ContinuousFilterState,
  PersonFilterState,
} from './person-filters';
import { Store } from '@ngrx/store';
import { PersonAndFamilyFilters, selectPersonFilters } from './person-filters.state';
import { Equals } from 'class-validator';
import { ComponentValidator } from 'app/common/component-validator';
import { cloneDeep } from 'lodash';
import { take, Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'gpf-person-filters',
  templateUrl: './person-filters.component.html',
  styleUrls: ['./person-filters.component.css'],
  standalone: false
})
export class PersonFiltersComponent extends ComponentValidator implements OnInit, OnDestroy {
  protected store: Store;
  private destroy$ = new Subject<void>();

  @Input() public dataset: Dataset;
  @Input() public isFamilyFilters: boolean;

  public selectedDatasetId: string;
  public categoricalFilters: PersonFilterState[] = [];
  public continuousFilters: PersonFilterState[] = [];

  @Equals(true, {message: 'Select at least one continuous filter.'})
  public areFiltersSelected = false;

  public constructor() {
    const store = inject(Store) as Store<object>;

    super(store, 'personFilters', selectPersonFilters);
    this.store = store;
  }

  public ngOnInit(): void {
    this.selectedDatasetId = this.dataset.id;

    // Initialize filters from state once during component initialization
    this.store.select(selectPersonFilters).pipe(take(1)).subscribe((state: PersonAndFamilyFilters) => {
      const clonedState = cloneDeep(state);
      this.setDefaultFilters();
      this.setFiltersFromState(clonedState);
    });

    this.store.select(selectPersonFilters).pipe(
      takeUntil(this.destroy$)
    ).subscribe((state: PersonAndFamilyFilters) => {
      if (this.isFamilyFilters) {
        this.areFiltersSelected = Boolean(state.familyFilters?.filter(f => f.sourceType === 'continuous').length);
      } else {
        this.areFiltersSelected = Boolean(state.personFilters?.filter(f => f.sourceType === 'continuous').length);
      }
    });

    super.ngOnInit();
  }

  public ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private setDefaultFilters(): void {
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
  }

  private setFiltersFromState(state: PersonAndFamilyFilters): void {
    const filters: PersonFilterState[] = this.isFamilyFilters ? state.familyFilters : state.personFilters;
    if (!filters) {
      return;
    }
    for (const filter of filters) {
      if (filter.sourceType === 'continuous') {
        const existingIndex = this.continuousFilters.findIndex(f => f.id ===filter.id);
        if (existingIndex !== -1) {
          this.continuousFilters[existingIndex] = filter;
        } else {
          this.continuousFilters.push(filter);
        }
      } else if (filter.sourceType === 'categorical') {
        const existingIndex = this.categoricalFilters.findIndex(f => f.id ===filter.id);
        if (existingIndex !== -1) {
          this.categoricalFilters[existingIndex] = filter;
        } else {
          this.categoricalFilters.push(filter);
        }
      } else {
        console.error(`Unexpected filter type:${filter.sourceType} in ${filter.id}`);
      }
    }
  }
}
