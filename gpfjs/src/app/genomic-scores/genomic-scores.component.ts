import { Component, Input, forwardRef, AfterViewInit, OnInit, OnDestroy } from '@angular/core';
import { Dataset, GenomicMetric } from '../datasets/datasets';
import { GenomicScoresService } from './genomic-scores.service';
import { GenomicScoresHistogramData } from './genomic-scores';

import { Observable } from 'rxjs/Observable';
import { Subscription } from 'rxjs/Subscription';
import { BehaviorSubject } from 'rxjs/BehaviorSubject';

import 'rxjs/add/operator/filter';

import { ValidationError } from 'class-validator';
import { GenomicScoreState } from './genomic-scores-store';
import { StateRestoreService } from '../store/state-restore.service';
import { DatasetsService } from '../datasets/datasets.service';

@Component({
  selector: 'gpf-genomic-scores',
  templateUrl: './genomic-scores.component.html',
})
export class GenomicScoresComponent implements OnInit, AfterViewInit, OnDestroy {
  @Input() index: number;
  @Input() genomicScoreState: GenomicScoreState;
  @Input() errors: string[];
  @Input() genomicMetrics: GenomicMetric[];

  private selectedMetric$ = new BehaviorSubject<GenomicMetric>(null);
  private selectedDataset$: Observable<Dataset>;
  private subscription: Subscription;

  constructor(
    private genomicsScoresService: GenomicScoresService,
    private datasetsService: DatasetsService
  ) {
  }

  chooseMetric(selectedMetric: GenomicMetric) {
    this.genomicScoreState.rangeStart = null;
    this.genomicScoreState.rangeEnd = null;
    this.selectedMetric = selectedMetric;
  }

  set selectedMetric(selectedMetric: GenomicMetric) {
    this.selectedMetric$.next(selectedMetric);
  }

  get selectedMetric() {
    return this.genomicScoreState.metric;
  }

  set rangeStart(range: number) {
    this.genomicScoreState.rangeStart = range;
  }

  get rangeStart() {
    return this.genomicScoreState.rangeStart;
  }

  set rangeEnd(range: number) {
    this.genomicScoreState.rangeEnd = range;
  }

  get rangeEnd() {
    return this.genomicScoreState.rangeEnd;
  }

  ngOnInit() {
      this.selectedDataset$ = this.datasetsService.getSelectedDataset();

      this.subscription = Observable.combineLatest(
          this.selectedMetric$.filter(m => !!m),
          this.selectedDataset$.filter(m => !!m)
        )
        .switchMap(([metric, dataset]) => {
          return this.genomicsScoresService
            .getHistogramData(dataset.id, metric.id);
        })
        .subscribe(histogramData => {
          let state = this.genomicScoreState;
          state.metric = this.selectedMetric$.value;
          state.histogramData = histogramData;
          state.domainMin = histogramData.bins[0];
          state.domainMax = histogramData.bins[histogramData.bins.length - 1];
        });
  }

  ngAfterViewInit() {
    if (this.genomicScoreState && this.genomicScoreState.metric) {
      this.selectedMetric = this.genomicMetrics
        .find(m => m.id === this.genomicScoreState.metric);
    }
  }

  ngOnDestroy() {
    if (this.subscription) {
      this.subscription.unsubscribe();
    }
  }
}
