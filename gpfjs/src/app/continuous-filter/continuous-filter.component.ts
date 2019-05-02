import { Component, OnInit, OnChanges, SimpleChanges, Input } from '@angular/core';
import { MeasuresService } from '../measures/measures.service';
import { HistogramData } from '../measures/measures';
import { ContinuousFilterState, ContinuousSelection } from '../pheno-filters/pheno-filters';
import { StateRestoreService } from '../store/state-restore.service';
import { Observable ,  Subject } from 'rxjs';
import { Partitions } from '../gene-weights/gene-weights';

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

    this.partitions
      .subscribe(partitions => {
        this.rangesCounts = [partitions.leftCount, partitions.midCount, partitions.rightCount];
      });
  }

  ngOnChanges(changes: SimpleChanges) {
    if (this.datasetId && this.measureName) {
      this.measuresService.getMeasureHistogram(this.datasetId, this.measureName)
        .subscribe(histogramData => {
          let selection = (this.continuousFilterState.selection as ContinuousSelection);
          this.histogramData = histogramData;
          if (!selection.min) {
            selection.min = histogramData.min;
          }
          if (!selection.max) {
            selection.max = histogramData.max;
          }
        });
    }
  }

  set rangeStart(value) {
    let selection = (this.continuousFilterState.selection as ContinuousSelection);
    selection.min = value;
    this.rangeChanges.next([
      this.datasetId,
      this.measureName,
      selection.min,
      selection.max
    ]);
  }

  get rangeStart(): number {
    return (this.continuousFilterState.selection as ContinuousSelection).min;
  }

  set rangeEnd(value) {
    let selection = (this.continuousFilterState.selection as ContinuousSelection);
    selection.max = value;
    this.rangeChanges.next([
      this.datasetId,
      this.measureName,
      selection.min,
      selection.max
    ]);
  }

  get rangeEnd(): number {
    return (this.continuousFilterState.selection as ContinuousSelection).max;
  }

}
