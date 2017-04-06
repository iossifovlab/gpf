import { Component, OnInit, Input, forwardRef } from '@angular/core';
import { MeasuresService } from '../measures/measures.service'
import { ContinuousMeasure } from '../measures/measures'
import { QueryStateCollector } from '../query/query-state-provider'
import { Store } from '@ngrx/store';
import {
  PhenoFiltersState, PHENO_FILTERS_ADD_CONTINUOUS,
  PHENO_FILTERS_CHANGE_CONTINUOUS_MEASURE, PHENO_FILTERS_CONTINUOUS_SET_MIN,
  PHENO_FILTERS_CONTINUOUS_SET_MAX
} from '../pheno-filters/pheno-filters';
import { Observable } from 'rxjs/Observable';
import { StateRestoreService } from '../store/state-restore.service'

@Component({
  selector: 'gpf-multi-continuous-filter',
  templateUrl: './multi-continuous-filter.component.html',
  styleUrls: ['./multi-continuous-filter.component.css'],
  providers: [{provide: QueryStateCollector, useExisting: forwardRef(() => MultiContinuousFilterComponent) }]
})
export class MultiContinuousFilterComponent extends QueryStateCollector implements OnInit {
  @Input() datasetId: string;
  @Input() continuousFilterConfig: any;

  measures: Array<ContinuousMeasure>;
  internalSelectedMeasure: ContinuousMeasure;

  private phenoFiltersState: Observable<PhenoFiltersState>;

  constructor(
    private store: Store<any>,
    private measuresService: MeasuresService,
    private stateRestoreService: StateRestoreService
  ) {
    super();
    this.phenoFiltersState = this.store.select('phenoFilters');
  }

  ngOnInit() {
    this.store.dispatch({
      'type': PHENO_FILTERS_ADD_CONTINUOUS,
      'payload': {
        'name': this.continuousFilterConfig.name,
        'role': this.continuousFilterConfig.measureFilter.role,
        'measure': null
      }
    });

    this.measuresService.getContinuousMeasures(this.datasetId).subscribe(
      (measures) => {
        this.measures = measures;

        this.stateRestoreService.state.subscribe(
          (state) => {
            if (state['phenoFilters']) {
              this.restoreContinuousFilter(state['phenoFilters']);
            }
          }
        )
      }
    )


    this.phenoFiltersState.subscribe(
      (filtersState) => {
        for (let filter of filtersState.phenoFilters) {
          if (filter.id == this.continuousFilterConfig.name) {
            if (!filter.measure) {
              this.internalSelectedMeasure = null;
              break;
            }

            if (this.measures) {
              for (let measure of this.measures) {
                if (measure.name == filter.measure) {
                  this.internalSelectedMeasure = measure;
                  break;
                }
              }
            }

            break;
          }
        }
      }
    );
  }

  restoreContinuousFilter(state) {
    for (let filter of state) {
      if (filter.id == this.continuousFilterConfig.name) {
        this.store.dispatch({
          'type': PHENO_FILTERS_CHANGE_CONTINUOUS_MEASURE,
          'payload': {
            'id': this.continuousFilterConfig.name,
            'measure': filter.measure,
            'domainMin': filter.domainMin,
            'domainMax': filter.domainMax
          }
        });
        break;
      }
    }
  }

  set selectedMeasure(measure) {
    this.store.dispatch({
      'type': PHENO_FILTERS_CHANGE_CONTINUOUS_MEASURE,
      'payload': {
        'id': this.continuousFilterConfig.name,
        'measure': measure.name,
        'domainMin': measure.min,
        'domainMax': measure.max
      }
    });
  }

  get selectedMeasure(): ContinuousMeasure {
    return this.internalSelectedMeasure;
  }

  clear() {
    this.store.dispatch({
      'type': PHENO_FILTERS_CHANGE_CONTINUOUS_MEASURE,
      'payload': {
        'id': this.continuousFilterConfig.name,
        'measure': null,
        'domainMin': 0,
        'domainMax': 0
      }
    });
  }

}
