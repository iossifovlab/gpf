import { Component, OnInit } from '@angular/core';
import { environment } from '../../environments/environment';

import { GenomicScoreState, GenomicScoresState } from '../genomic-scores/genomic-scores-store';
import { GenomicScoresBlockService } from './genomic-scores-block.service';
import { GenomicScores } from './genomic-scores-block';
import { Store} from '@ngxs/store';
import { SetGenomicScores, GenomicScoresBlockState } from './genomic-scores-block.state';
import { combineLatest, of } from 'rxjs';
import { switchMap, take } from 'rxjs/operators';
import { StatefulComponent } from 'app/common/stateful-component';
import { ValidateNested } from 'class-validator';

@Component({
  selector: 'gpf-genomic-scores-block',
  templateUrl: './genomic-scores-block.component.html',
  styleUrls: ['./genomic-scores-block.component.css'],
})
export class GenomicScoresBlockComponent extends StatefulComponent implements OnInit {
  @ValidateNested()
  genomicScoresState = new GenomicScoresState();
  scores = [];
  genomicScoresArray: GenomicScores[];

  constructor(
    protected store: Store,
    private genomicScoresBlockService: GenomicScoresBlockService,
  ) {
    super(store, GenomicScoresBlockState, 'genomicScores');
  }

  ngOnInit() {
    super.ngOnInit();
    this.genomicScoresBlockService.getGenomicScores().pipe(
      take(1),
      switchMap(genomicScores => {
        return combineLatest(
          of(genomicScores),
          this.store.selectOnce(state => state.genomicScoresBlockState)
        )
      })
    ).subscribe(([genomicScores, state]) => {
      this.genomicScoresArray = genomicScores;
      if (state.genomicScores.length > 0) {
        // restore state
        for (const score of state.genomicScores) {
          const genomicScore = new GenomicScoreState();
          genomicScore.score = this.genomicScoresArray
                                   .find(el => el['score'] === score['metric']);
          genomicScore.rangeStart = score['rangeStart'];
          genomicScore.rangeEnd = score['rangeEnd'];
          genomicScore.domainMin = genomicScore.score.bins[0];
          genomicScore.domainMax =
            genomicScore.score.bins[genomicScore.score.bins.length - 1];
          this.addFilter(genomicScore);
        }
      }
    });
  }

  get imgPathPrefix() {
    return environment.imgPathPrefix;
  }

  trackById(index: number, data: any) {
    return data.score.score;
  }

  addFilter(genomicScoreState: GenomicScoreState = null) {
    if (!genomicScoreState) {
      genomicScoreState = new GenomicScoreState(this.genomicScoresArray[0]);
    }
    this.genomicScoresState.genomicScoresState.push(genomicScoreState);
  }

  removeFilter(genomicScore: GenomicScoreState) {
    this.genomicScoresState.genomicScoresState = this.genomicScoresState
        .genomicScoresState.filter(gs => gs !== genomicScore);
  }

  updateState() {
    const newState = this.genomicScoresState.genomicScoresState
      .filter(el => el.score)
      .map(el => {
        return {
          metric: el.score.score,
          rangeStart: el.rangeStart,
          rangeEnd: el.rangeEnd
        };
    });
    this.store.dispatch(new SetGenomicScores(newState));
  }
}
