import { Component, OnInit, OnChanges, Input } from '@angular/core';
import { MeasuresService } from '../measures/measures.service';
import { HistogramData } from '../measures/measures';
import { ContinuousFilterState, ContinuousSelection } from '../person-filters/person-filters';
import { Observable, Subject } from 'rxjs';
import { Partitions } from '../gene-scores/gene-scores';
import { debounceTime, distinctUntilChanged, switchMap, take } from 'rxjs/operators';
import { cloneDeep } from 'lodash';
import { Store } from '@ngrx/store';
import { ComponentValidator } from 'app/common/component-validator';
import { selectPersonFilters, updateFamilyFilter, updatePersonFilter } from 'app/person-filters/person-filters.state';

@Component({
  selector: 'gpf-continuous-filter',
  templateUrl: './continuous-filter.component.html'
})
export class ContinuousFilterComponent extends ComponentValidator implements OnInit, OnChanges {
  private rangeChanges = new Subject<[string, string, number, number]>();
  private partitions: Observable<Partitions>;

  @Input() public datasetId: string;
  @Input() public measureName: string;
  @Input() public continuousFilter: ContinuousFilterState;
  @Input() public isFamilyFilters: boolean;

  private continuousFilterState: ContinuousFilterState;
  public histogramData: HistogramData;

  public rangesCounts: Array<number>;

  public constructor(
    private measuresService: MeasuresService,
    protected store: Store,
  ) {
    super(store, 'personFilters', selectPersonFilters);
  }

  public ngOnInit(): void {
    this.partitions = this.rangeChanges.pipe(
      debounceTime(500),
      distinctUntilChanged(),
      switchMap(([datasetId, measureName, internalRangeStart, internalRangeEnd]) => this.measuresService
        .getMeasurePartitions(datasetId, measureName, internalRangeStart, internalRangeEnd))
    );

    this.partitions.subscribe(partitions => {
      this.rangesCounts = [partitions.leftCount, partitions.midCount, partitions.rightCount];
    });

    this.store.select(selectPersonFilters).pipe(take(1)).subscribe(state => {
      let stateFilter: ContinuousFilterState;

      if (this.isFamilyFilters) {
        stateFilter = state.familyFilters?.find(filter => filter.id === this.continuousFilter.id);
      } else {
        stateFilter = state.personFilters?.find(filter => filter.id === this.continuousFilter.id);
      }

      if (stateFilter) {
        this.continuousFilterState = cloneDeep(stateFilter);
      } else {
        this.continuousFilterState = cloneDeep(this.continuousFilter);
      }
    });
  }

  public ngOnChanges(): void {
    if (this.datasetId && this.measureName) {
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
    (this.continuousFilterState.selection as ContinuousSelection).min = value;

    if (this.isFamilyFilters) {
      this.store.dispatch(updateFamilyFilter({familyFilter: cloneDeep(this.continuousFilterState)}));
    } else {
      this.store.dispatch(updatePersonFilter({personFilter: cloneDeep(this.continuousFilterState)}));
    }

    this.rangeChanges.next([
      this.datasetId,
      this.measureName,
      (this.continuousFilterState.selection as ContinuousSelection).min,
      (this.continuousFilterState.selection as ContinuousSelection).max
    ]);
  }

  public get rangeStart(): number {
    return (this.continuousFilterState.selection as ContinuousSelection).min;
  }

  public set rangeEnd(value) {
    (this.continuousFilterState.selection as ContinuousSelection).max = value;

    if (this.isFamilyFilters) {
      this.store.dispatch(updateFamilyFilter({familyFilter: cloneDeep(this.continuousFilterState)}));
    } else {
      this.store.dispatch(updatePersonFilter({personFilter: cloneDeep(this.continuousFilterState)}));
    }

    this.rangeChanges.next([
      this.datasetId,
      this.measureName,
      (this.continuousFilterState.selection as ContinuousSelection).min,
      (this.continuousFilterState.selection as ContinuousSelection).max
    ]);
  }

  public get rangeEnd(): number {
    return (this.continuousFilterState.selection as ContinuousSelection).max;
  }
}
