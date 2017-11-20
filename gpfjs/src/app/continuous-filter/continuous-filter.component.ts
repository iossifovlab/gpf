import { Component, OnInit, OnChanges, Input } from '@angular/core';
import { MeasuresService } from '../measures/measures.service';
import { HistogramData } from '../measures/measures';
import { ContinuousFilterState, PhenoFiltersState } from '../pheno-filters/pheno-filters';
import { StateRestoreService } from '../store/state-restore.service';
import { Observable } from 'rxjs/Observable';
import { Subject }           from 'rxjs/Subject';
import { Partitions } from '../gene-weights/gene-weights';
import { validateOrReject } from 'class-validator';
import { plainToClass } from 'class-transformer';
import { ValidationError } from 'class-validator';

@Component({
  selector: 'gpf-continuous-filter',
  templateUrl: './continuous-filter.component.html',
  styleUrls: ['./continuous-filter.component.css']
})
export class ContinuousFilterComponent implements OnInit, OnChanges {
  private rangeChanges = new Subject<[string, string, number, number]>();
  private partitions: Observable<Partitions>;

  @Input() filterId: string;
  @Input() datasetId: string;
  @Input() measureName: string;
  @Input() continuousFilterState: ContinuousFilterState;
  histogramData: HistogramData;

  rangesCounts: Array<number>;


  constructor(
    private measuresService: MeasuresService,
    private stateRestoreService: StateRestoreService
  ) {
  }

  ngOnInit() {
    this.partitions = this.rangeChanges
      .debounceTime(100)
      .distinctUntilChanged()
      .switchMap(([datasetId, measureName, internalRangeStart, internalRangeEnd]) => {
        return this.measuresService
          .getMeasurePartitions(datasetId, measureName, internalRangeStart, internalRangeEnd);
      });

    this.partitions.subscribe(
      (partitions) => {
        this.rangesCounts = [partitions.leftCount, partitions.midCount, partitions.rightCount];
    });
  }

  restoreContinuousFilter(state) {
    let filter = state.find(f => f.id === this.filterId);
    if (filter && filter.measure === this.measureName) {
      this.rangeStart = filter.mmin;
      this.rangeEnd = filter.mmax;
    }
  }

  ngOnChanges() {
    if (this.datasetId && this.measureName) {
      this.measuresService.getMeasureHistogram(this.datasetId, this.measureName).subscribe(
        (histogramData) => {
          this.histogramData = histogramData;
          this.continuousFilterState.mmin = histogramData.min;
          this.continuousFilterState.mmax = histogramData.max;

          this.stateRestoreService.getState(this.constructor.name + this.filterId)
            .take(1)
            .subscribe(state => {
              if (state['phenoFilters']) {
                this.restoreContinuousFilter(state['phenoFilters']);
              }
            });
        });
    }
  }

  set rangeStart(value) {
    this.continuousFilterState.mmin = value;
    this.rangeChanges.next([
      this.datasetId,
      this.measureName,
      this.continuousFilterState.mmin,
      this.continuousFilterState.mmax
    ]);
  }

  get rangeStart(): number {
    return this.continuousFilterState.mmin;
  }

  set rangeEnd(value) {
    this.continuousFilterState.mmax = value;
    this.rangeChanges.next([
      this.datasetId,
      this.measureName,
      this.continuousFilterState.mmin,
      this.continuousFilterState.mmax
    ]);
  }

  get rangeEnd(): number {
    return this.continuousFilterState.mmax;
  }

}
