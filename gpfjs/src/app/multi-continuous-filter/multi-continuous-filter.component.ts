import { Component, OnInit, Input, forwardRef, ViewChild } from '@angular/core';
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
  @ViewChild("inputGroup") inputGroupSpan: any;
  @ViewChild("searchBox") searchBox: any;

  measures: Array<ContinuousMeasure>;
  filteredMeasures: Array<ContinuousMeasure>;
  internalSelectedMeasure: ContinuousMeasure;
  searchString: string;

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
        this.searchBoxChange('');

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
        'measure': measure  ? measure.name : null,
        'domainMin': measure ? measure.min : 0,
        'domainMax': measure ? measure.max : 0
      }
    });
  }

  get selectedMeasure(): ContinuousMeasure {
    return this.internalSelectedMeasure;
  }

  clear() {
    this.selectedMeasure = null;
    this.searchBox.nativeElement.value = '';
    this.searchBoxChange('');
  }

  onFocus(event) {
    event.stopPropagation();
    this.inputGroupSpan.nativeElement.classList.add("show");
    this.selectedMeasure = null;
  }

  searchBoxChange(searchFieldValue) {
    this.searchString = searchFieldValue;

    this.filteredMeasures = this.measures.filter(
      (value) => {
        return ~value.name.indexOf(searchFieldValue);
      }
    )
  }

}
