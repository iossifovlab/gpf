import { Component, OnChanges, Input, OnInit } from '@angular/core';
import { Dataset, PersonFilter } from '../datasets/datasets';
import { PersonFilterState, CategoricalFilterState, ContinuousFilterState } from './person-filters';
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

  private personFiltersState = new Array<[PersonFilter, PersonFilterState]>();

  @Select(PersonFiltersState) state$: Observable<PersonFiltersModel>;
  errors: Array<string> = [];

  constructor(private store: Store) { }

  ngOnChanges(changes) {
    this.personFiltersState = this.filters.map(personFilter => {
      let filterState = null;
      if (personFilter.sourceType === 'continuous') {
        if (personFilter.from === 'pedigree') {
          throw new Error('Continuous filters with pedigree sources are not supported!');
        }
        filterState = new ContinuousFilterState(
          personFilter.name, personFilter.sourceType, personFilter.role, personFilter.source, personFilter.from,
        );
      } else if (personFilter.sourceType === 'categorical') {
        filterState = new CategoricalFilterState(
          personFilter.name, personFilter.sourceType, personFilter.role, personFilter.source, personFilter.from,
        );
      }
      return [personFilter, filterState] as [PersonFilter, PersonFilterState];
    });
  }

  ngOnInit() {
    this.state$.subscribe(state => {
      // validate for errors
      console.log(state);
      validate(this).then(errors => this.errors = errors.map(err => String(err)));
    });
  }

  get categoricalFilters() {
    return this.personFiltersState.filter(
      ([_, personFilter]) => personFilter && personFilter.sourceType === 'categorical'
    );
  }

  get continuousFilters() {
    return this.personFiltersState.filter(
      ([_, personFilter]) => personFilter && personFilter.sourceType === 'continuous'
    );
  }

  updateFilters() {
    const filters = this.personFiltersState.map(f => f[1]).filter(f => f && !f.isEmpty());
    if (this.isFamilyFilters) {
      this.store.dispatch(new SetFamilyFilters(filters));
    } else {
      this.store.dispatch(new SetPersonFilters(filters));
    }
  }
}
