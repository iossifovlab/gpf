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
  styleUrls: ['./genomic-scores.component.css'],
})
export class GenomicScoresComponent {
  @Input() public index: number;
  @Input() public genomicScoreState: GenomicScoreState;
  @Input() public errors: string[];
  @Input() public genomicScoresArray: GenomicScores[];
  @Output() public updateGenomicScoreEvent = new EventEmitter();

  private rangeChanges = new ReplaySubject<[string, number, number]>(1);

  public imgPathPrefix = environment.imgPathPrefix;

  public constructor(private modalService: NgbModal) {}

  public showHelp(): void {
    const modalRef = this.modalService.open(PopupComponent, {
      size: 'lg',
      centered: true
    });
    modalRef.componentInstance.data = this.genomicScoreState.score.help;
  }

  public set rangeStart(range: number) {
    this.genomicScoreState.rangeStart = range;
    this.updateGenomicScoreEvent.emit();
  }

  public get rangeStart(): number {
    return this.genomicScoreState.rangeStart;
  }

  public set rangeEnd(range: number) {
    this.genomicScoreState.rangeEnd = range;
    this.updateGenomicScoreEvent.emit();
  }

  public get rangeEnd(): number {
    return this.genomicScoreState.rangeEnd;
  }

  public get domainMin(): number {
    return this.genomicScoreState.domainMin;
  }

  public get domainMax(): number {
    return this.genomicScoreState.domainMax;
  }

  private updateLabels(): void {
    this.rangeChanges.next([
      this.genomicScoreState.score.score,
      this.genomicScoreState.rangeStart,
      this.genomicScoreState.rangeEnd
    ]);
  }

  public set selectedGenomicScores(selectedGenomicScores: GenomicScores) {
    this.genomicScoreState.score = selectedGenomicScores;
    this.genomicScoreState.rangeStart = null;
    this.genomicScoreState.rangeEnd = null;
    this.genomicScoreState.changeDomain(selectedGenomicScores);
    this.updateLabels();
    this.updateGenomicScoreEvent.emit();
  }

  public get selectedGenomicScores(): GenomicScores {
    return this.genomicScoreState.score;
  }
}
