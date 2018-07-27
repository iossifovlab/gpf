import { Component, Input } from '@angular/core';
import { GenomicScores } from '../genomic-scores-block/genomic-scores-block';

import 'rxjs/add/operator/filter';

import { GenomicScoreState } from './genomic-scores-store';

import { ReplaySubject } from 'rxjs/ReplaySubject';

@Component({
  selector: 'gpf-genomic-scores',
  templateUrl: './genomic-scores.component.html',
})
export class GenomicScoresComponent {
  @Input() index: number;
  @Input() genomicScoreState: GenomicScoreState;
  @Input() errors: string[];
  @Input() genomicScoresArray: GenomicScores[];

  private rangeChanges = new ReplaySubject<[string, number, number]>(1);

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

  private updateLabels() {
    this.rangeChanges.next([
      this.genomicScoreState.score.score,
      this.genomicScoreState.rangeStart,
      this.genomicScoreState.rangeEnd
    ]);
  }

  set selectedGenomicScores(selectedGenomicScores: GenomicScores) {
    this.genomicScoreState.score = selectedGenomicScores;
    this.genomicScoreState.rangeStart = null;
    this.genomicScoreState.rangeEnd = null;
    this.genomicScoreState.domainMin = selectedGenomicScores.bins[0];
    this.genomicScoreState.domainMax =
      selectedGenomicScores.bins[selectedGenomicScores.bins.length - 1];
    this.updateLabels();
  }

  get selectedGenomicScores() {
    return this.genomicScoreState.score;
  }
}
