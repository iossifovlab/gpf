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
            personFilter.name, personFilter.sourceType, personFilter.role, personFilter.source,
          );
        } else if (personFilter.sourceType === 'categorical') {
          filterState = new CategoricalFilterState(
            personFilter.name, personFilter.sourceType, personFilter.role, personFilter.source,
          );
        }
        return [personFilter, filterState] as [PersonFilter, PersonFilterState];
      });
  }

  get categoricalPhenoFilters() {
    return this.personFiltersState.filter(
      ([_, personFilter]) => personFilter && personFilter.sourceType === 'categorical'
    );
  }

  get continuousPhenoFilters() {
    return this.personFiltersState.filter(
      ([_, personFilter]) => personFilter && personFilter.sourceType === 'continuous'
    );
  }

  getState() {
    return this.validateAndGetState(this.personFiltersState)
      .map(personFiltersState => ({
        personFilters: personFiltersState.map(x => x[1]).filter(f => f && !f.isEmpty())
      }));
  }

}
