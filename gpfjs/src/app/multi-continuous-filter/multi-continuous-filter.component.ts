import { Component, OnInit, Input, forwardRef } from '@angular/core';
import { MeasuresService } from '../measures/measures.service'
import { ContinuousMeasure } from '../measures/measures'
import { QueryStateCollector } from '../query/query-state-provider'
import { Store } from '@ngrx/store';
import {
  PhenoFiltersState, PHENO_FILTERS_ADD_CONTINUOUS,
  PHENO_FILTERS_CHANGE_MEASURE
} from '../pheno-filters/pheno-filters';
import { Observable } from 'rxjs/Observable';

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
    private measuresService: MeasuresService
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

  set selectedMeasure(measure) {
    this.store.dispatch({
      'type': PHENO_FILTERS_CHANGE_MEASURE,
      'payload': {
        'id': this.continuousFilterConfig.name,
        'measure': measure.name
      }
    });
  }

  get selectedMeasure(): ContinuousMeasure {
    return this.internalSelectedMeasure;
  }

  clear() {
    this.store.dispatch({
      'type': PHENO_FILTERS_CHANGE_MEASURE,
      'payload': {
        'id': this.continuousFilterConfig.name,
        'measure': null
      }
    });
  }

}
