import { Component, OnInit, Input } from '@angular/core';
import { MeasuresService } from '../measures/measures.service'
import { HistogramData } from '../measures/measures'
import { Store } from '@ngrx/store';
import {
  PhenoFiltersState, PHENO_FILTERS_ADD_CATEGORICAL,
  PHENO_FILTERS_CONTINUOUS_SET_MIN, PHENO_FILTERS_CONTINUOUS_SET_MAX
} from '../pheno-filters/pheno-filters';
@Component({
  selector: 'gpf-continuous-filter',
  templateUrl: './continuous-filter.component.html',
  styleUrls: ['./continuous-filter.component.css']
})
export class ContinuousFilterComponent implements OnInit {
  @Input() filterId: string;
  @Input() datasetId: string;
  @Input() measureName: string;
  histogramData: HistogramData;

  internalRangeStart: number;
  internalRangeEnd: number;

  rangesCounts = [0, 0, 0];

  constructor(
    private measuresService: MeasuresService,
    private store: Store<any>
  ) { }

  ngOnInit() {
  }

  ngOnChanges() {
    if (this.datasetId && this.measureName) {
      this.measuresService.getMeasureHistogram(this.datasetId, this.measureName).subscribe(
        (histogramData) => {
          this.histogramData = histogramData;
          this.rangeStart = histogramData.min;
          this.rangeEnd = histogramData.max;
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
    this.internalRangeStart = value;
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
    this.internalRangeEnd = value;
  }

  get rangeEnd(): number {
    return this.internalRangeEnd;
  }

}
