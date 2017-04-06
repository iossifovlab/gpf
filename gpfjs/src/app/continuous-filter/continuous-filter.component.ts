import { Component, OnInit, Input } from '@angular/core';
import { MeasuresService } from '../measures/measures.service'
import { HistogramData } from '../measures/measures'
import { Store } from '@ngrx/store';
import {
  ContinuousFilterState, PhenoFiltersState, PHENO_FILTERS_ADD_CATEGORICAL,
  PHENO_FILTERS_CONTINUOUS_SET_MIN, PHENO_FILTERS_CONTINUOUS_SET_MAX
} from '../pheno-filters/pheno-filters';
import { StateRestoreService } from '../store/state-restore.service'
import { Observable } from 'rxjs/Observable';
import { Subject }           from 'rxjs/Subject';
import { Partitions } from '../gene-weights/gene-weights';

@Component({
  selector: 'gpf-continuous-filter',
  templateUrl: './continuous-filter.component.html',
  styleUrls: ['./continuous-filter.component.css']
})
export class ContinuousFilterComponent implements OnInit {
  private rangeChanges = new Subject<[string, string, number, number]>();
  private partitions: Observable<Partitions>;

  @Input() filterId: string;
  @Input() datasetId: string;
  @Input() measureName: string;
  histogramData: HistogramData;

  internalRangeStart: number;
  internalRangeEnd: number;

  rangesCounts: Array<number>;

  private phenoFiltersState: Observable<PhenoFiltersState>;

  constructor(
    private measuresService: MeasuresService,
    private store: Store<any>,
    private stateRestoreService: StateRestoreService
  ) {
    this.phenoFiltersState = this.store.select('phenoFilters');
  }

  ngOnInit() {


    this.phenoFiltersState.subscribe(
      (filtersState) => {
        for (let filter of filtersState.phenoFilters) {
          let categoricalFilter = filter as ContinuousFilterState;
          if (filter.id == this.filterId) {
            this.internalRangeStart = categoricalFilter.mmin;
            this.internalRangeEnd = categoricalFilter.mmax;

            this.rangeChanges.next([
              this.datasetId,
              this.measureName,
              this.internalRangeStart,
              this.internalRangeEnd
            ]);
          }
        }
      }
    );

    this.partitions = this.rangeChanges
      .debounceTime(100)
      .distinctUntilChanged()
      .switchMap(([datasetId, measureName, internalRangeStart, internalRangeEnd]) => {
        return this.measuresService
          .getMeasurePartitions(datasetId, measureName, internalRangeStart, internalRangeEnd);
      })
      .catch(error => {
        console.log(error);
        return null;
      });

    this.partitions.subscribe(
      (partitions) => {
        this.rangesCounts = [partitions.leftCount, partitions.midCount, partitions.rightCount];
    });
  }

  restoreContinuousFilter(state) {
    for (let filter of state) {
      if (filter.id == this.filterId) {
        this.store.dispatch({
          'type': PHENO_FILTERS_CONTINUOUS_SET_MIN,
          'payload': {
            'id': this.filterId,
            'value': filter.mmin
          }
        });

        this.store.dispatch({
          'type': PHENO_FILTERS_CONTINUOUS_SET_MAX,
          'payload': {
            'id': this.filterId,
            'value': filter.mmax
          }
        });

        break;
      }
    }
  }

  ngOnChanges() {
    if (this.datasetId && this.measureName) {
      this.measuresService.getMeasureHistogram(this.datasetId, this.measureName).subscribe(
        (histogramData) => {
          this.histogramData = histogramData;
          this.rangeStart = histogramData.min;
          this.rangeEnd = histogramData.max;

          this.stateRestoreService.state.subscribe(
            (state) => {
              if (state['phenoFilters']) {
                this.restoreContinuousFilter(state['phenoFilters']);
              }
            }
          )
        }
      )
    }
  }

  set rangeStart(value) {
    this.store.dispatch({
      'type': PHENO_FILTERS_CONTINUOUS_SET_MIN,
      'payload': {
        'id': this.filterId,
        'value': value
      }
    });
  }

  get rangeStart(): number {
    return this.internalRangeStart;
  }

  set rangeEnd(value) {
    this.store.dispatch({
      'type': PHENO_FILTERS_CONTINUOUS_SET_MAX,
      'payload': {
        'id': this.filterId,
        'value': value
      }
    });
  }

  get rangeEnd(): number {
    return this.internalRangeEnd;
  }

}
