import { Component, OnInit } from '@angular/core';
import { environment } from '../../environments/environment';

import { GenomicScoreState, GenomicScoresState } from '../genomic-scores/genomic-scores-store';
import { GenomicScoresBlockService } from './genomic-scores-block.service';
import { GenomicScores } from './genomic-scores-block';
import { Store, Select } from '@ngxs/store';
import { SetGenomicScores, GenomicScoresBlockModel, GenomicScoresBlockState } from './genomic-scores-block.state';
import { Observable } from 'rxjs';
import { validate } from 'class-validator';

@Component({
  selector: 'gpf-genomic-scores-block',
  templateUrl: './genomic-scores-block.component.html',
  styleUrls: ['./genomic-scores-block.component.css'],
})
export class GenomicScoresBlockComponent implements OnInit {
  genomicScoresState = new GenomicScoresState();
  scores = [];
  genomicScoresArray: GenomicScores[];

  @Select(GenomicScoresBlockState) state$: Observable<GenomicScoresBlockModel>;
  errors: Array<string> = [];

  constructor(
    private genomicScoresBlockService: GenomicScoresBlockService,
    private store: Store,
  ) { }

  ngOnInit() {
    this.genomicScoresBlockService.getGenomicScores()
    .take(1)
    .subscribe(genomicScores => {
      this.genomicScoresArray = genomicScores;
    });

    this.store.selectOnce(state => state.genomicScoresBlockState).subscribe(state => {
      // restore state
      if (state['genomicScores'] && state['genomicScores'].length > 0) {
        for (const score of state['genomicScores']) {
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

    this.state$.subscribe(state => {
      // validate for errors
      validate(this.genomicScoresState).then(errors => this.errors = errors.map(err => String(err)));
    });
  }

  get imgPathPrefix() {
    return environment.imgPathPrefix;
  }

  trackById(index: number, data: any) {
    return data.id;
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
