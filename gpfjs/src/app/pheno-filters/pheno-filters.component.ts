import { Component, OnChanges, Input, forwardRef } from '@angular/core';
import { Dataset, PhenoFilter } from '../datasets/datasets';
import { QueryStateProvider } from '../query/query-state-provider';
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
export class PhenoFiltersComponent extends QueryStateProvider implements OnChanges {
  @Input() dataset: Dataset;

  private phenoFiltersState = new Array<[PhenoFilter, PhenoFilterState]>();
  errors: string[];
  flashingAlert = false;

  constructor() {
    super();
  }

  ngOnChanges() {
    if (!this.dataset) {
      return;
    }

    this.phenoFiltersState =
      this.dataset.genotypeBrowser.phenoFilters
      .concat(this.dataset.genotypeBrowser.familyStudyFilters)
      .map(phenoFilter => {
        if (phenoFilter.measureType === 'continuous') {
          return [
            phenoFilter, plainToClass(ContinuousFilterState, phenoFilter)
          ] as [PhenoFilter, PhenoFilterState];
        }

        return [
          phenoFilter, plainToClass(CategoricalFilterState, phenoFilter)
        ] as [PhenoFilter, PhenoFilterState];

      })
      .filter(([_, f]) => !f.isEmpty());
  }

  get categoricalPhenoFilters() {
    if (this.phenoFiltersState.length === 0) {
      return null;
    }

    return this.phenoFiltersState.filter(
      ([_, phenoFilter]) => phenoFilter.measureType === 'categorical'
    );
  }

  get continuousPhenoFilters() {
    if (this.phenoFiltersState.length === 0) {
      return null;
    }

    return this.phenoFiltersState.filter(
      ([_, phenoFilter]) => phenoFilter.measureType === 'continuous'
    );
  }

  getState() {
    return toValidationObservable(this.phenoFiltersState)
      .map(phenoFiltersState => ({
        phenoFilters: {
          phenoFilters: phenoFiltersState.map(x => x[1])
        }
      }))
      .catch(errors => {
        this.errors = validationErrorsToStringArray(errors);
        this.flashingAlert = true;
        setTimeout(() => { this.flashingAlert = false; }, 1000);
        return Observable.throw(`${this.constructor.name}: invalid state`);
      });
  }

}
