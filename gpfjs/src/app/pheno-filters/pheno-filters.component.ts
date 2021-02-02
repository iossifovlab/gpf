import { Component, OnChanges, Input, forwardRef } from '@angular/core';
import { Dataset, PersonFilter } from '../datasets/datasets';
import { QueryStateProvider, QueryStateWithErrorsProvider } from '../query/query-state-provider';
import { PersonFilterState, CategoricalFilterState, ContinuousFilterState } from './pheno-filters';

@Component({
  selector: 'gpf-pheno-filters',
  templateUrl: './pheno-filters.component.html',
  styleUrls: ['./pheno-filters.component.css'],
  providers: [{
    provide: QueryStateProvider,
    useExisting: forwardRef(() => PhenoFiltersComponent)
  }]
})
export class PhenoFiltersComponent extends QueryStateWithErrorsProvider implements OnChanges {
  @Input() dataset: Dataset;
  @Input() filters;

  private personFiltersState = new Array<[PersonFilter, PersonFilterState]>();

  constructor() {
    super();
  }

  ngOnChanges(changes) {
    if (!this.dataset) {
      return;
    }

    this.personFiltersState =
      this.filters
      .map(personFilter => {
        if (personFilter.sourceType === 'continuous') {
          const continuousFilterState = new ContinuousFilterState(
            personFilter.name,
            personFilter.sourceType,
            personFilter.role,
            personFilter.source,
          );
          return [
            personFilter, continuousFilterState
          ] as [PersonFilter, PersonFilterState];
        } else if (personFilter.sourceType === 'categorical') {
          const categoricalFilterState = new CategoricalFilterState(
            personFilter.name,
            personFilter.sourceType,
            personFilter.role,
            personFilter.source,
          );

          return [
            personFilter, categoricalFilterState
          ] as [PersonFilter, PersonFilterState];

          }

          return [personFilter, null] as [PersonFilter, PersonFilterState];

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
