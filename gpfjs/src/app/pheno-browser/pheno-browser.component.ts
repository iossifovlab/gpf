import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Params, Router } from '@angular/router';

import { Observable } from 'rxjs';
import { Subject } from 'rxjs/Subject';

import { PhenoBrowserService } from './pheno-browser.service';
import { PhenoInstruments, PhenoInstrument, PhenoMeasures } from './pheno-browser';

@Component({
  selector: 'gpf-pheno-browser',
  templateUrl: './pheno-browser.component.html',
  styleUrls: ['./pheno-browser.component.css']
})
export class PhenoBrowserComponent implements OnInit {

  private selectedChanges$: Subject<PhenoInstrument> = new Subject<PhenoInstrument>();
  private measuresToShow: Observable<PhenoMeasures>;

  private datasetId: string;
  private instruments: Observable<PhenoInstruments>;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private phenoBrowserService: PhenoBrowserService
  ) { }


  ngOnInit() {
    this.route.parent.params.take(1).subscribe(
      (params: Params) => {
        this.datasetId = params['dataset'];
        this.initInstruments(this.datasetId);
      }
    );
    this.measuresToShow = this.selectedChanges$
      .switchMap((newSelection) => this.phenoBrowserService.getMeasures(this.datasetId, newSelection))
      .share();

  }

  initInstruments(datasetId: string): void {
    this.instruments = this.phenoBrowserService
      .getInstruments(datasetId).share();

    this.instruments.take(1).subscribe((phenoInstruments) => {
      this.emitInstrument(phenoInstruments.default);
    });
  }

  emitInstrument(instrument: PhenoInstrument) {
    this.selectedChanges$.next(instrument);
  }
}
