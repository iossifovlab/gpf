import { Component, OnChanges, Input, OnInit } from '@angular/core';
import { Dataset, PersonFilter } from '../datasets/datasets';
import { PersonFilterState, CategoricalFilterState, ContinuousFilterState, ContinuousSelection, CategoricalSelection } from './person-filters';
import { validate } from 'class-validator';
import { Observable } from 'rxjs';
import { Store, Select } from '@ngxs/store';
import { SetFamilyFilters, SetPersonFilters, PersonFiltersModel, PersonFiltersState } from './person-filters.state';

@Component({
  selector: 'gpf-person-filters',
  templateUrl: './person-filters.component.html',
  styleUrls: ['./person-filters.component.css'],
})
export class PersonFiltersComponent implements OnChanges, OnInit {
  @Input() dataset: Dataset;
  @Input() filters: PersonFilter[];
  @Input() isFamilyFilters: boolean;

  private personFiltersState = new Map<string, PersonFilterState>();

  @Select(PersonFiltersState) state$: Observable<PersonFiltersModel>;
  errors: Array<string> = [];

  constructor(private store: Store) { }

  ngOnChanges(changes) {
    this.store.selectOnce(state => state.personFiltersState).subscribe(state => {
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

      // restore state
      const filterStates = this.isFamilyFilters ? state.familyFilters : state.personFilters;
      if (filterStates.length) {
        for (const filterState of filterStates) {
          const filterType = filterState.sourceType === 'continuous' ? ContinuousFilterState : CategoricalFilterState;
          let selection = null;
          if (filterState.sourceType === 'continuous') {
            selection = new ContinuousSelection(
              filterState.selection.min,
              filterState.selection.max,
              filterState.selection.domainMin,
              filterState.selection.domainMax,
            )
          } else {
            selection = new CategoricalSelection(filterState.selection.selection)
          }
          const newFilter = new filterType(
            filterState.id, filterState.sourceType, filterState.role,
            filterState.source, filterState.from, selection
          )
          this.personFiltersState.set(filterState.id, newFilter);
        }
      }
    });
  }

  ngOnInit() {
    this.state$.subscribe(state => {
      // validate for errors
      validate(this).then(errors => this.errors = errors.map(err => String(err)));
    });
  }

  get categoricalFilters() {
    return [...this.personFiltersState]
      .map(([_, personFilter]) => personFilter)
      .filter(personFilter => personFilter && personFilter.sourceType === 'categorical');
  }

  get continuousFilters() {
    const res = [...this.personFiltersState]
      .map(([_, personFilter]) => personFilter)
      .filter(personFilter => personFilter && personFilter.sourceType === 'continuous');
    return res;
  }

  getFilter(filterName: string) {
    return this.filters.find(f => f.name === filterName);
  }

  updateFilters() {
    const filters = [...this.personFiltersState]
      .map(([_, personFilter]) => personFilter)
      .filter(personFilter => personFilter && !personFilter.isEmpty());
    if (this.isFamilyFilters) {
      this.store.dispatch(new SetFamilyFilters(filters));
    } else {
      this.store.dispatch(new SetPersonFilters(filters));
    }
  }
}
