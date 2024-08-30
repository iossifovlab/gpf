import { Component, OnChanges, Input, OnInit } from '@angular/core';
import { Dataset, PersonFilter } from '../datasets/datasets';
import { PersonFilterState, CategoricalFilterState, ContinuousFilterState, ContinuousSelection, CategoricalSelection } from './person-filters';
import { Store } from '@ngrx/store';
import { selectPersonFilters, setFamilyFilters, setPersonFilters } from './person-filters.state';
import { IsNotEmpty, ValidateNested } from 'class-validator';
import { selectDatasetId } from 'app/datasets/datasets.state';
import { take } from 'rxjs';
import { StatefulComponentNgRx } from 'app/common/stateful-component_ngrx';

@Component({
  selector: 'gpf-person-filters',
  templateUrl: './person-filters.component.html',
  styleUrls: ['./person-filters.component.css'],
})
export class PersonFiltersComponent extends StatefulComponentNgRx implements OnChanges, OnInit {
  @Input() public dataset: Dataset;
  @Input() public filters: PersonFilter[];
  @Input() public isFamilyFilters: boolean;

  public selectedDatasetId: string;

  @IsNotEmpty({message: 'Select at least one continuous filter.'})
  public selected = false;

  @ValidateNested({each: true})
  private personFiltersState = new Map<string, PersonFilterState>();

  public constructor(protected store: Store) {
    super(store, 'personFilters', selectPersonFilters);
  }

  public ngOnInit(): void {
    this.store.select(selectDatasetId).pipe(take(1)).subscribe(datasetId => {
      this.selectedDatasetId = datasetId;
    });
  }

  public ngOnChanges(): void {
    this.store.select(selectPersonFilters).pipe(take(1)).subscribe(state => {
      // set default state
      for (const filter of this.filters) {
        let filterState = null;
        if (filter.sourceType === 'continuous') {
          if (filter.from === 'pedigree') {
            throw new Error('Continuous filters with pedigree sources are not supported!');
          }
          filterState = new ContinuousFilterState(
            filter.name, filter.sourceType, filter.role, filter.source, filter.from,
          );
        } else if (filter.sourceType === 'categorical') {
          filterState = new CategoricalFilterState(
            filter.name, filter.sourceType, filter.role, filter.source, filter.from,
          );
        }
        this.personFiltersState.set(filter.name, filterState);
      }

      // // restore state
      // const filterStates: PersonFilterState[] = this.isFamilyFilters ? state.familyFilters : state.personFilters;
      // if (filterStates.length) {
      //   for (const filterState of filterStates) {
      //     const filterType = filterState.sourceType === 'continuous' ? ContinuousFilterState : CategoricalFilterState;
      //     let selection = null;
      //     if (filterState.sourceType === 'continuous') {
      //       const filterStateSelection = filterState.selection as ContinuousSelection;
      //       selection = new ContinuousSelection(
      //         filterStateSelection.min,
      //         filterStateSelection.max,
      //         filterStateSelection.domainMin,
      //         filterStateSelection.domainMax,
      //       );
      //     } else {
      //       selection = new CategoricalSelection((filterState.selection as CategoricalSelection).selection);
      //     }
      //     const newFilter = new filterType(
      //       filterState.id, filterState.sourceType, filterState.role,
      //       filterState.source, filterState.from, selection
      //     );
      //     this.personFiltersState.set(filterState.id, newFilter);
      //   }
      // }
    });
    this.updateFilters();
  }

  public get categoricalFilters(): PersonFilterState[] {
    return [...this.personFiltersState]
      .map(([_, personFilter]) => personFilter)
      .filter(personFilter => personFilter && personFilter.sourceType === 'categorical');
  }

  public get continuousFilters(): PersonFilterState[] {
    return [...this.personFiltersState]
      .map(([_, personFilter]) => personFilter)
      .filter(personFilter => personFilter && personFilter.sourceType === 'continuous');
  }

  public getFilter(filterName: string): PersonFilter {
    return this.filters.find(f => f.name === filterName);
  }

  public updateFilters(): void {
    this.updateSelected();
    const filters = [...this.personFiltersState]
      .map(([_, personFilter]) => personFilter)
      .filter(personFilter => personFilter && !personFilter.isEmpty());

    console.log(this.filters)
    if (this.isFamilyFilters) {
      this.store.dispatch(setFamilyFilters({familyFilters: filters}));
    } else {
      this.store.dispatch(setPersonFilters({personFilters: filters}));
    }
  }

  public updateSelected(): void {
    this.selected = null;
    this.personFiltersState.forEach(el => {
      if (!el.isEmpty()) {
        this.selected = true;
      }
    });
  }
}
