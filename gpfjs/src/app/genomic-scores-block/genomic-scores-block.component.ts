import { Component, OnInit } from '@angular/core';
import { GenomicScoreLocalState } from '../genomic-scores/genomic-scores-store';
import { GenomicScoresBlockService } from './genomic-scores-block.service';
import { CategoricalHistogram, GenomicScore } from './genomic-scores-block';
import { Store} from '@ngrx/store';
import { selectGenomicScores, setGenomicScores } from './genomic-scores-block.state';
import { combineLatest, of } from 'rxjs';
import { switchMap, take } from 'rxjs/operators';
import { ValidateNested } from 'class-validator';
import { ComponentValidator } from 'app/common/component-validator';

@Component({
  selector: 'gpf-genomic-scores-block',
  templateUrl: './genomic-scores-block.component.html',
  styleUrls: ['./genomic-scores-block.component.css'],
})
export class GenomicScoresBlockComponent extends ComponentValidator implements OnInit {
  @ValidateNested({
    each: true
  })
  public genomicScoresLocalState: GenomicScoreLocalState[] = [];
  public genomicScoresArray: GenomicScore[];

  public constructor(
    protected store: Store,
    private genomicScoresBlockService: GenomicScoresBlockService,
  ) {
    super(store, 'genomicScores', selectGenomicScores);
  }

  public ngOnInit(): void {
    super.ngOnInit();
    this.genomicScoresBlockService.getGenomicScores().pipe(
      take(1),
      switchMap(genomicScores => combineLatest([
        of(genomicScores),
        this.store.select(selectGenomicScores)
      ]))
    ).pipe(take(1)).subscribe(([genomicScores, genomicScoresState]) => {
      this.genomicScoresArray = genomicScores;
      if (genomicScoresState.length > 0) {
        // restore state
        for (const score of genomicScoresState) {
          this.genomicScoresLocalState.push(score);
        }
      }
    });
  }

  public addFilter(): void {
    const firstScore = new GenomicScoreLocalState();
    firstScore.score = this.genomicScoresArray[0].score;
    if (this.genomicScoresArray[0].histogram instanceof CategoricalHistogram) {
      firstScore.histogramType = 'categorical';
      firstScore.rangeStart = 0;
      firstScore.rangeEnd = 0;
      firstScore.values = this.genomicScoresArray[0].histogram.values.map(value => value.name);
      firstScore.categoricalView = 'range selector';
    } else {
      firstScore.histogramType = 'continuous';
      firstScore.rangeStart = this.genomicScoresArray[0].histogram.rangeMin;
      firstScore.rangeEnd = this.genomicScoresArray[0].histogram.rangeMax;
      firstScore.values = null;
      firstScore.categoricalView = null;
    }
    this.genomicScoresLocalState.push(firstScore);
  }

  public removeFilter(genomicScore: GenomicScoreLocalState): void {
    this.genomicScoresLocalState = this.genomicScoresLocalState.filter(gs => gs !== genomicScore);
    this.updateState();
  }

  public updateState(): void {
    this.store.dispatch(setGenomicScores({genomicScores: this.genomicScoresLocalState}));
  }
}
