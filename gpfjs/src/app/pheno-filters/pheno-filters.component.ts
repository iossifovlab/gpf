import { Component, OnChanges, Input, forwardRef } from '@angular/core';
import { Dataset, PhenoFilter } from '../datasets/datasets';
import { QueryStateProvider, QueryStateWithErrorsProvider } from '../query/query-state-provider';
import { toValidationObservable, validationErrorsToStringArray } from '../utils/to-observable-with-validation';
import {
  PhenoFilterState, PhenoFiltersState, CategoricalFilterState,
  ContinuousFilterState
} from './pheno-filters';

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

  private phenoFiltersState = new Array<[PhenoFilter, PhenoFilterState]>();

  constructor() {
    super();
  }

  ngOnChanges(changes) {
    if (!this.dataset) {
      return;
    }

    this.phenoFiltersState =
      this.dataset.genotypeBrowserConfig.phenoFilters
      .concat(this.dataset.genotypeBrowserConfig.familyFilters || [])
      .map(phenoFilter => {
        console.log(phenoFilter);
        if (phenoFilter.measureType === 'continuous') {
          const continuousFilterState = new ContinuousFilterState(
            phenoFilter.name,
            phenoFilter.measureType,
            phenoFilter.measureFilter.role,
            phenoFilter.measureFilter.measure,
          );
          return [
            phenoFilter, continuousFilterState
          ] as [PhenoFilter, PhenoFilterState];
        } else if (phenoFilter.measureType === 'categorical') {
          const categoricalFilterState = new CategoricalFilterState(
            phenoFilter.name,
            phenoFilter.measureType,
            phenoFilter.measureFilter.role,
            phenoFilter.measureFilter.measure,
          );

          return [
            phenoFilter, categoricalFilterState
          ] as [PhenoFilter, PhenoFilterState];

          }

          return [phenoFilter, null] as [PhenoFilter, PhenoFilterState];

      });
  }

  get categoricalPhenoFilters() {
    return this.phenoFiltersState.filter(
      ([_, phenoFilter]) => phenoFilter && phenoFilter.measureType === 'categorical'
    );
  }

  get continuousPhenoFilters() {
    return this.phenoFiltersState.filter(
      ([_, phenoFilter]) => phenoFilter && phenoFilter.measureType === 'continuous'
    );
  }

  getState() {
    return this.validateAndGetState(this.phenoFiltersState)
      .map(phenoFiltersState => ({
        phenoFilters: phenoFiltersState.map(x => x[1]).filter(f => f && !f.isEmpty())
      }));
  }

}
