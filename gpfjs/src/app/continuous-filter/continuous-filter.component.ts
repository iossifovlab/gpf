import { Component, OnInit, OnChanges, Input, Output, EventEmitter } from '@angular/core';
import { MeasuresService } from '../measures/measures.service';
import { HistogramData } from '../measures/measures';
import { ContinuousFilterState, ContinuousSelection } from '../person-filters/person-filters';
import { Observable, Subject } from 'rxjs';
import { Partitions } from '../gene-scores/gene-scores';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import { cloneDeep } from 'lodash';

@Component({
  selector: 'gpf-continuous-filter',
  templateUrl: './continuous-filter.component.html'
})
export class ContinuousFilterComponent implements OnInit, OnChanges {
  private rangeChanges = new Subject<[string, string, number, number]>();
  private partitions: Observable<Partitions>;

  @Input() public datasetId: string;
  @Input() public measureName: string;
  @Input() public continuousFilterState: ContinuousFilterState;
  @Output() public updateFilterEvent = new EventEmitter<ContinuousFilterState>();
  public histogramData: HistogramData;

  public rangesCounts: Array<number>;

  public constructor(private measuresService: MeasuresService) { }

  public ngOnInit(): void {
    this.continuousFilterState = new ContinuousFilterState(
      this.continuousFilterState.id,
      this.continuousFilterState.sourceType,
      this.continuousFilterState.role,
      this.continuousFilterState.source,
      this.continuousFilterState.from,
      new ContinuousSelection(
        (this.continuousFilterState.selection as ContinuousSelection).min,
        (this.continuousFilterState.selection as ContinuousSelection).max,
        (this.continuousFilterState.selection as ContinuousSelection).domainMin,
        (this.continuousFilterState.selection as ContinuousSelection).domainMax,
      )
    );

    this.partitions = this.rangeChanges.pipe(
      debounceTime(100),
      distinctUntilChanged(),
      switchMap(([datasetId, measureName, internalRangeStart, internalRangeEnd]) => this.measuresService
        .getMeasurePartitions(datasetId, measureName, internalRangeStart, internalRangeEnd))
    );

    this.partitions.subscribe(partitions => {
      this.rangesCounts = [partitions.leftCount, partitions.midCount, partitions.rightCount];
    });
    if (this.continuousFilterState !== undefined) {
      this.continuousFilterState.selection = new ContinuousSelection(null, null, null, null);
    }
  }

  public ngOnChanges(): void {
    if (this.datasetId && this.measureName) {
      this.continuousFilterState = new ContinuousFilterState(
        this.continuousFilterState.id,
        this.continuousFilterState.sourceType,
        this.continuousFilterState.role,
        this.continuousFilterState.source,
        this.continuousFilterState.from,
        new ContinuousSelection(
          (this.continuousFilterState.selection as ContinuousSelection).min,
          (this.continuousFilterState.selection as ContinuousSelection).max,
          (this.continuousFilterState.selection as ContinuousSelection).domainMin,
          (this.continuousFilterState.selection as ContinuousSelection).domainMax,
        )
      );

      this.measuresService.getMeasureHistogram(this.datasetId, this.measureName)
        .subscribe(histogramData => {
          const selection = this.continuousFilterState.selection as ContinuousSelection;
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

  public set rangeStart(value) {
    const updatedState = cloneDeep(this.continuousFilterState);
    const selection = updatedState.selection as ContinuousSelection;
    selection.min = value;
    this.continuousFilterState = updatedState;
    this.updateFilterEvent.emit(this.continuousFilterState);
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
    const updatedState = cloneDeep(this.continuousFilterState);
    const selection = updatedState.selection as ContinuousSelection;
    selection.max = value;
    this.continuousFilterState = updatedState;
    this.updateFilterEvent.emit(this.continuousFilterState);
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
