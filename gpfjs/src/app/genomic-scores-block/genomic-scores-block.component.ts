import { Component, OnInit } from '@angular/core';
import { GenomicScoreState, GenomicScoresState } from '../genomic-scores/genomic-scores-store';
import { GenomicScoresBlockService } from './genomic-scores-block.service';
import { GenomicScores } from './genomic-scores-block';
import { Store} from '@ngrx/store';
import { selectGenomicScores, setGenomicScores } from './genomic-scores-block.state';
import { combineLatest, of } from 'rxjs';
import { switchMap, take } from 'rxjs/operators';
import { ValidateNested } from 'class-validator';
import { StatefulComponent } from 'app/common/stateful-component';

@Component({
  selector: 'gpf-genomic-scores-block',
  templateUrl: './genomic-scores-block.component.html',
  styleUrls: ['./genomic-scores-block.component.css'],
})
export class GenomicScoresBlockComponent extends StatefulComponent implements OnInit {
  @ValidateNested()
  public genomicScoresState = new GenomicScoresState();
  public genomicScoresArray: GenomicScores[];

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
      switchMap(genomicScores => combineLatest(
        of(genomicScores),
        this.store.select(selectGenomicScores)
      ))
    ).pipe(take(1)).subscribe(([genomicScores, genomicScoresState]) => {
      this.genomicScoresArray = genomicScores;
      if (genomicScoresState.length > 0) {
        // restore state
        for (const score of genomicScoresState) {
          const genomicScore = new GenomicScoreState();
          genomicScore.score = this.genomicScoresArray.find(el => el.score === score['metric']);
          genomicScore.rangeStart = score['rangeStart'];
          genomicScore.rangeEnd = score['rangeEnd'];
          genomicScore.domainMin = genomicScore.score.bins[0];
          genomicScore.domainMax =
            genomicScore.score.bins[genomicScore.score.bins.length - 1];
          this.genomicScoresState.genomicScoresState.push(genomicScore);
        }
      }
    });
  }

  public addFilter(): void {
    this.genomicScoresState.genomicScoresState.push(
      new GenomicScoreState(this.genomicScoresArray[0])
    );
  }

  public removeFilter(genomicScore: GenomicScoreState): void {
    this.genomicScoresState.genomicScoresState = this.genomicScoresState
      .genomicScoresState.filter(gs => gs !== genomicScore);
    this.updateState();
  }

  public updateState(): void {
    const newState = this.genomicScoresState.genomicScoresState
      .filter(el => el.score)
      .map(el => ({
        metric: el.score.score,
        rangeStart: el.rangeStart,
        rangeEnd: el.rangeEnd
      }));

    this.store.dispatch(setGenomicScores({genomicScores: newState}));
  }
}
