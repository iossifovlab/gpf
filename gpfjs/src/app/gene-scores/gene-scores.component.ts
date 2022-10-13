import { Component, OnInit, ViewEncapsulation } from '@angular/core';
import { Partitions, GeneScoresLocalState, GeneScores } from './gene-scores';
import { GeneScoresService } from './gene-scores.service';
// eslint-disable-next-line no-restricted-imports
import { ReplaySubject ,  Observable, combineLatest, of } from 'rxjs';

import { Store } from '@ngxs/store';
import { ConfigService } from '../config/config.service';

import { SetGeneScore, SetHistogramValues, GeneScoresState } from './gene-scores.state';
import { catchError, debounceTime, distinctUntilChanged, map, switchMap } from 'rxjs/operators';
import { StatefulComponent } from 'app/common/stateful-component';
import { ValidateNested } from 'class-validator';
import { environment } from 'environments/environment';

@Component({
  encapsulation: ViewEncapsulation.None, // TODO: What is this?
  selector: 'gpf-gene-scores',
  templateUrl: './gene-scores.component.html',
})
export class GeneScoresComponent extends StatefulComponent implements OnInit {
  private rangeChanges = new ReplaySubject<[string, number, number]>(1);
  private partitions: Observable<Partitions>;

  geneScoresArray: GeneScores[];
  rangesCounts: Observable<Array<number>>;
  public downloadUrl: string;

  @ValidateNested()
  geneScoresLocalState = new GeneScoresLocalState();

  public imgPathPrefix = environment.imgPathPrefix;

  constructor(
    protected store: Store,
    private geneScoresService: GeneScoresService,
    private config: ConfigService,
  ) {
    super(store, GeneScoresState, 'geneScores');
    this.partitions = this.rangeChanges.pipe(
      debounceTime(100),
      distinctUntilChanged(),
      switchMap(([score, internalRangeStart, internalRangeEnd]) => {
        return this.geneScoresService.getPartitions(score, internalRangeStart, internalRangeEnd);
      }),
      catchError(error => {
        console.warn(error);
        return of(null);
      })
    );

    this.rangesCounts = this.partitions.pipe(map((partitions) => {
       return [partitions.leftCount, partitions.midCount, partitions.rightCount];
    }));
  }

  ngOnInit() {
    super.ngOnInit();
    this.geneScoresService.getGeneScores().pipe(
      switchMap(geneScores => {
        return combineLatest([
          of(geneScores),
          this.store.selectOnce(GeneScoresState)
        ]);
      })
    ).subscribe(([geneScores, state]) => {
      this.geneScoresArray = geneScores;
      // restore state
      // console.log(state);
      if (state.geneScore !== null) {
        for (const geneScore of this.geneScoresArray) {
          if (geneScore.score === state.geneScore.score) {
            this.selectedGeneScores = geneScore;
            this.rangeStart = state.rangeStart;
            this.rangeEnd = state.rangeEnd;
            break;
          }
        }
      } else {
        this.selectedGeneScores = this.geneScoresArray[0];
      }
    });
    if(this.geneScoresLocalState.score !== null && this.rangeStart !== null && this.rangeEnd !== null) {
        this.updateHistogramState();
    }
}

  private updateLabels() {
    this.rangeChanges.next([
      this.geneScoresLocalState.score.score,
      this.rangeStart,
      this.rangeEnd
    ]);
    //console.log(this.geneScoresLocalState.score.score ,this.rangeStart, this.rangeEnd);
  }

  updateHistogramState() {
    this.updateLabels();
    this.store.dispatch(new SetHistogramValues(
      this.geneScoresLocalState.rangeStart,
      this.geneScoresLocalState.rangeEnd,
    ));
    console.log(this.geneScoresLocalState.rangeStart, this.geneScoresLocalState.rangeEnd);
  }

  get selectedGeneScores() {
    return this.geneScoresLocalState.score;
  }

  set selectedGeneScores(selectedGeneScores: GeneScores) {
    this.geneScoresLocalState.score = selectedGeneScores;
    this.rangeStart = null;
    this.rangeEnd = null;
    this.changeDomain(selectedGeneScores);
    this.updateLabels();
    this.downloadUrl = this.getDownloadUrl();
    this.store.dispatch(new SetGeneScore(this.geneScoresLocalState.score));
  }

  set rangeStart(range: number) {
    this.geneScoresLocalState.rangeStart = range;
    this.updateHistogramState();
  }

  get rangeStart() {
    return this.geneScoresLocalState.rangeStart;
  }

  set rangeEnd(range: number) {
    this.geneScoresLocalState.rangeEnd = range;
    this.updateHistogramState();
  }

  get rangeEnd() {
    return this.geneScoresLocalState.rangeEnd;
  }

  getDownloadUrl(): string {
    return `${this.config.baseUrl}gene_scores/download/${this.selectedGeneScores.score}`;
  }

  changeDomain(scores: GeneScores) {
    if (scores.domain !== null) {
      this.geneScoresLocalState.domainMin = scores.domain[0];
      this.geneScoresLocalState.domainMax = scores.domain[1];
    } else {
      this.geneScoresLocalState.domainMin = scores.bins[0];
      this.geneScoresLocalState.domainMax = scores.bins[scores.bins.length - 1];
    }
  }
}
