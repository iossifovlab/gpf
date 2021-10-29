import { Component, OnInit, OnChanges, SimpleChanges, Input, Output, EventEmitter } from '@angular/core';
import { MeasuresService } from '../measures/measures.service';
import { HistogramData } from '../measures/measures';
import { ContinuousFilterState, ContinuousSelection } from '../person-filters/person-filters';
// tslint:disable-next-line:import-blacklist
import { Observable, Subject } from 'rxjs';
import { Partitions } from '../gene-weights/gene-weights';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';

@Component({
  selector: 'gpf-continuous-filter',
  templateUrl: './continuous-filter.component.html',
  styleUrls: ['./continuous-filter.component.css']
})
export class ContinuousFilterComponent implements OnInit, OnChanges {
  private rangeChanges = new Subject<[string, string, number, number]>();
  private partitions: Observable<Partitions>;

  @Input() public filterId: string;
  @Input() public datasetId: string;
  @Input() public measureName: string;
  @Input() public continuousFilterState: ContinuousFilterState;
  @Output() public updateFilterEvent = new EventEmitter();
  public histogramData: HistogramData;

  public rangesCounts: Array<number>;

  constructor(private measuresService: MeasuresService) { }

  public ngOnInit(): void {
    this.partitions = this.rangeChanges.pipe(
      debounceTime(100),
      distinctUntilChanged(),
      switchMap(([datasetId, measureName, internalRangeStart, internalRangeEnd]) => {
        return this.measuresService
          .getMeasurePartitions(datasetId, measureName, internalRangeStart, internalRangeEnd);
      })
    );

    this.partitions.subscribe(partitions => {
      this.rangesCounts = [partitions.leftCount, partitions.midCount, partitions.rightCount];
    });
    this.continuousFilterState.selection = new ContinuousSelection(null, null, null, null);
  }

  public ngOnChanges(changes: SimpleChanges): void {
    if (this.datasetId && this.measureName) {
      this.measuresService.getMeasureHistogram(this.datasetId, this.measureName)
        .subscribe(histogramData => {
          const selection = (this.continuousFilterState.selection as ContinuousSelection);
          this.histogramData = histogramData;
          if (!selection.min) {
            selection.min = histogramData.min;
          }
          if (!selection.max) {
            selection.max = histogramData.max;
          }
        });
    }

    if (!this.measureName) {
      const selection = (this.continuousFilterState.selection as ContinuousSelection);
      selection.min = null;
      selection.domainMin = null;
      selection.max = null;
      selection.domainMax = null;
    }
  }

  public set rangeStart(value) {
    const selection = (this.continuousFilterState.selection as ContinuousSelection);
    selection.min = value;
    this.updateFilterEvent.emit();
    this.rangeChanges.next([
      this.datasetId,
      this.measureName,
      selection.min,
      selection.max
    ]);
  }

  public get rangeStart(): number {
    return (this.continuousFilterState.selection as ContinuousSelection).min;
  }

  public set rangeEnd(value) {
    const selection = (this.continuousFilterState.selection as ContinuousSelection);
    selection.max = value;
    this.updateFilterEvent.emit();
    this.rangeChanges.next([
      this.datasetId,
      this.measureName,
      selection.min,
      selection.max
    ]);
  }

  public get rangeEnd(): number {
    return (this.continuousFilterState.selection as ContinuousSelection).max;
  }

}
