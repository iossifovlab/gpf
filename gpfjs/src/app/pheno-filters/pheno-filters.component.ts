import { Component, OnChanges, Input, forwardRef } from '@angular/core';
import { Dataset, PhenoFilter } from '../datasets/datasets';
import { QueryStateProvider, QueryStateWithErrorsProvider } from '../query/query-state-provider';
import { toValidationObservable, validationErrorsToStringArray } from '../utils/to-observable-with-validation';
import {
  PhenoFilterState, PhenoFiltersState, CategoricalFilterState,
  ContinuousFilterState
} from './pheno-filters';
import { Observable } from 'rxjs/Observable';
import { ValidationError, validateOrReject } from 'class-validator';
import { plainToClass } from 'class-transformer';

@Component({
  selector: 'gpf-pheno-filters',
  templateUrl: './pheno-filters.component.html',
  styleUrls: ['./pheno-filters.component.css'],
  providers: [{provide: QueryStateProvider, useExisting: forwardRef(() => PhenoFiltersComponent) }]
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
      this.dataset.genotypeBrowser.phenoFilters
      .concat(this.dataset.genotypeBrowser.familyStudyFilters || [])
      .map(phenoFilter => {
        if (phenoFilter.measureType === 'continuous') {
          return [
            phenoFilter, plainToClass(ContinuousFilterState, phenoFilter)
          ] as [PhenoFilter, PhenoFilterState];
        }
        console.log(phenoFilter);
        const categoricalFilterState = new CategoricalFilterState(
          phenoFilter.name,
          phenoFilter.measureType,
          phenoFilter.measureFilter.role,
          phenoFilter.measureFilter.measure,
        );

        return [
          phenoFilter, categoricalFilterState
        ] as [PhenoFilter, PhenoFilterState];

      });

    console.log(this.phenoFiltersState);
  }

  get categoricalPhenoFilters() {
    return this.phenoFiltersState.filter(
      ([_, phenoFilter]) => phenoFilter.measureType === 'categorical'
    );
  }

  get continuousPhenoFilters() {
    return this.phenoFiltersState.filter(
      ([_, phenoFilter]) => phenoFilter.measureType === 'continuous'
    );
  }

  getState() {
    return this.validateAndGetState(this.phenoFiltersState)
      .map(phenoFiltersState => ({
        phenoFilters: phenoFiltersState.map(x => x[1]).filter(f => !f.isEmpty())
      }));
  }

}
