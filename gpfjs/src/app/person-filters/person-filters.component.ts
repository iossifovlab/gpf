import { Component, OnChanges, Input, forwardRef } from '@angular/core';
import { Dataset, PersonFilter } from '../datasets/datasets';
import { QueryStateProvider, QueryStateWithErrorsProvider } from '../query/query-state-provider';
import { PersonFilterState, CategoricalFilterState, ContinuousFilterState } from './person-filters';

@Component({
  selector: 'gpf-person-filters',
  templateUrl: './person-filters.component.html',
  styleUrls: ['./person-filters.component.css'],
  providers: [{
    provide: QueryStateProvider,
    useExisting: forwardRef(() => PersonFiltersComponent)
  }]
})
export class PersonFiltersComponent extends QueryStateWithErrorsProvider implements OnChanges {
  @Input() dataset: Dataset;
  @Input() filters: PersonFilter[];
  @Input() isFamilyFilters: boolean;

  private personFiltersState = new Array<[PersonFilter, PersonFilterState]>();

  constructor() {
    super();
  }

  ngOnChanges(changes) {
    this.personFiltersState =
      this.filters.map(personFilter => {
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

  getState() {
    const keyName = this.isFamilyFilters ? 'familyFilters' : 'personFilters';
    return this.validateAndGetState(this.personFiltersState).map(personFiltersState => {
      const result = {};
      result[keyName] = personFiltersState.map(x => x[1]).filter(f => f && !f.isEmpty());
      return result;
    });
  }
}
