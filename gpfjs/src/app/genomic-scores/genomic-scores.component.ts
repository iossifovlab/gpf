import { Component, Input, Output, EventEmitter, OnInit } from '@angular/core';
import { environment } from 'environments/environment';
import { ReplaySubject } from 'rxjs';
import {
  CategoricalHistogram,
  CategoricalHistogramView,
  GenomicScore,
  NumberHistogram
} from '../genomic-scores-block/genomic-scores-block';
import { GenomicScoreLocalState } from './genomic-scores-store';
import { ArrayNotEmpty } from 'class-validator';
import { cloneDeep } from 'lodash';
import { Store } from '@ngrx/store';
import { setGenomicScoresCategorical } from 'app/genomic-scores-block/genomic-scores-block.state';

@Component({
  selector: 'gpf-genomic-scores',
  templateUrl: './genomic-scores.component.html',
})
export class GenomicScoresComponent implements OnInit {
  @Input() public index: number;
  @Input() public genomicScoreState: GenomicScoreLocalState;
  @Input() public errors: string[];
  @Input() public genomicScoresArray: GenomicScore[];
  @Output() public updateGenomicScoreEvent = new EventEmitter();
  public selectedGenomicScore: GenomicScore;

  @ArrayNotEmpty({message: 'Please select at least one bar.'})
  public categoricalValues: string[] = [];
  public selectedCategoricalHistogramView: CategoricalHistogramView = 'range selector';

  private rangeChanges = new ReplaySubject<[string, number, number]>(1);

  public imgPathPrefix = environment.imgPathPrefix;

  public constructor(
    protected store: Store
  ) { }

  public ngOnInit(): void {
    if (!this.genomicScoreState.score) {
      this.selectedGenomicScore = this.genomicScoresArray[0];
    } else {
      this.selectedGenomicScore = this.genomicScoresArray.find(score => score.score === this.genomicScoreState.score);
    }
  }

  public updateRangeStart(range): void {
    this.genomicScoreState.rangeStart = range as number;
    this.updateGenomicScoreEvent.emit();
  }

  public updateRangeEnd(range): void {
    this.genomicScoreState.rangeEnd = range as number;
    this.updateGenomicScoreEvent.emit();
  }

  public get domainMin(): number {
    return (this.selectedGenomicScore.histogram as NumberHistogram).bins[0];
  }

  public get domainMax(): number {
    const lastIndex = (this.selectedGenomicScore.histogram as NumberHistogram).bins.length - 1;
    return (this.selectedGenomicScore.histogram as NumberHistogram).bins[lastIndex];
  }

  private updateLabels(): void {
    this.rangeChanges.next([
      this.genomicScoreState.score,
      this.genomicScoreState.rangeStart,
      this.genomicScoreState.rangeEnd
    ]);
  }

  public updateSelectedGenomicScore(selectedGenomicScore: GenomicScore): void {
    this.genomicScoreState.score = selectedGenomicScore.score;
    this.genomicScoreState.rangeStart = null;
    this.genomicScoreState.rangeEnd = null;
    this.updateLabels();
    this.updateGenomicScoreEvent.emit();
  }

  public toggleCategoricalValues(values: string[]): void {
    values.forEach(value => {
      const valueIndex = this.categoricalValues.findIndex(v => v === value);
      if (valueIndex === -1) {
        this.categoricalValues.push(value);
      } else {
        this.categoricalValues.splice(valueIndex, 1);
      }
    });
    this.store.dispatch(setGenomicScoresCategorical({
      score: this.genomicScoreState.score,
      values: cloneDeep(this.categoricalValues),
      categoricalView: this.selectedCategoricalHistogramView,
    }));
  }

  public isNumberHistogram(arg: object): arg is NumberHistogram {
    return arg instanceof NumberHistogram;
  }

  public isCategoricalHistogram(arg: object): arg is CategoricalHistogram {
    return arg instanceof CategoricalHistogram;
  }
}
