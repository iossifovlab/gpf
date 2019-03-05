import { Component, OnInit, Input, ViewEncapsulation } from '@angular/core';
import { ActivatedRoute, Params, Router } from '@angular/router';

import { Observable ,  BehaviorSubject } from 'rxjs';

import { PhenoBrowserService } from './pheno-browser.service';
import { PhenoInstruments, PhenoInstrument, PhenoMeasures } from './pheno-browser';

@Component({
  selector: 'gpf-pheno-browser',
  templateUrl: './pheno-browser.component.html',
  styleUrls: ['./pheno-browser.component.css'],
})
export class PhenoBrowserComponent implements OnInit {

  selectedInstrument$: BehaviorSubject<PhenoInstrument> = new BehaviorSubject<PhenoInstrument>(undefined);
  measuresToShow$: Observable<PhenoMeasures>;

  instruments: Observable<PhenoInstruments>;
  downloadLink$: Observable<string>;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private phenoBrowserService: PhenoBrowserService,
  ) { }

  ngOnInit() {
    let datasetId$ = this.route.parent.params
      .take(1)
      .map(params => <string>params['dataset']);

    this.initInstruments(datasetId$);
    this.initMeasuresToShow(datasetId$);
    this.initDownloadLink(datasetId$);
  }

  initMeasuresToShow(datasetId$: Observable<string>) {
    this.measuresToShow$ = Observable
      .combineLatest([this.selectedInstrument$, datasetId$])
      .switchMap(([newSelection, datasetId]) => {
        return this.phenoBrowserService.getMeasures(datasetId, newSelection)
      }).share();
  }

  initInstruments(datasetId$: Observable<string>): void {
    this.instruments = datasetId$.switchMap(datasetId =>
      this.phenoBrowserService.getInstruments(datasetId)).share();

    this.instruments.take(1).subscribe((phenoInstruments) => {
      this.emitInstrument(phenoInstruments.default);
    });
  }

  emitInstrument(instrument: PhenoInstrument) {
    this.selectedInstrument$.next(instrument);
  }

  initDownloadLink(datasetId$: Observable<string>) {
    this.downloadLink$ = Observable
      .combineLatest([this.selectedInstrument$, datasetId$])
      .map(([instrument, datasetId]) =>
        this.phenoBrowserService.getDownloadLink(instrument, datasetId)
      );
  }
}
