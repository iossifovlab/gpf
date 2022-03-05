import { Component, Input, Output, EventEmitter } from '@angular/core';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { environment } from 'environments/environment';
// eslint-disable-next-line no-restricted-imports
import { ReplaySubject } from 'rxjs';

import { GenomicScores } from '../genomic-scores-block/genomic-scores-block';
import { PopupComponent } from '../popup/popup.component';
import { GenomicScoreState } from './genomic-scores-store';

@Component({
  selector: 'gpf-genomic-scores',
  templateUrl: './genomic-scores.component.html',
})
export class GenomicScoresComponent {
  @Input() index: number;
  @Input() genomicScoreState: GenomicScoreState;
  @Input() errors: string[];
  @Input() genomicScoresArray: GenomicScores[];
  @Output() updateGenomicScoreEvent = new EventEmitter();

  private rangeChanges = new ReplaySubject<[string, number, number]>(1);

  public imgPathPrefix = environment.imgPathPrefix;

  constructor(private modalService: NgbModal) {}

  showHelp() {
    const modalRef = this.modalService.open(PopupComponent, {
      size: 'lg'
    });
    modalRef.componentInstance.data = this.genomicScoreState.score.help;
  }

  set rangeStart(range: number) {
    this.genomicScoreState.rangeStart = range;
    this.updateGenomicScoreEvent.emit();
  }

  get rangeStart() {
    return this.genomicScoreState.rangeStart;
  }

  set rangeEnd(range: number) {
    this.genomicScoreState.rangeEnd = range;
    this.updateGenomicScoreEvent.emit();
  }

  get rangeEnd() {
    return this.genomicScoreState.rangeEnd;
  }

  get domainMin() {
    return this.genomicScoreState.domainMin;
  }

  get domainMax() {
    return this.genomicScoreState.domainMax;
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
    this.genomicScoreState.changeDomain(selectedGenomicScores);
    this.updateLabels();
    this.updateGenomicScoreEvent.emit();
  }

  get selectedGenomicScores() {
    return this.genomicScoreState.score;
  }
}
