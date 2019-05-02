import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Location } from '@angular/common';

import { Observable, BehaviorSubject, ReplaySubject } from 'rxjs';

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

  input$ = new ReplaySubject<string>(1);

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private phenoBrowserService: PhenoBrowserService,
    private location: Location,
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
    this.measuresToShow$ = this.input$
      .map(searchTerm => searchTerm.trim())
      .debounceTime(300)
      .distinctUntilChanged()
      .combineLatest(this.selectedInstrument$, datasetId$)
      .do(([searchTerm, newSelection, datasetId]) => {
        let queryParamsObject: any = {};
        if (newSelection) {
          queryParamsObject.instrument = newSelection;
        }
        if (searchTerm) {
          queryParamsObject.search = searchTerm;
        }
        let url = this.router.createUrlTree(['.'], {
          relativeTo: this.route,
          replaceUrl: true,
          queryParams: queryParamsObject
        }).toString();
        this.location.go(url);
      })
      .switchMap(([searchTerm, newSelection, datasetId]) => {
        return this.phenoBrowserService.getMeasures(datasetId, newSelection, searchTerm);
      })
      .share();

    this.route.queryParamMap
      .map(params => [params.get('instrument') || '',  params.get('search') || ''])
      .take(1)
      .subscribe(([instrument, queryTerm]) => {
        this.search(queryTerm);
        this.emitInstrument(instrument);
      });
  }

  initInstruments(datasetId$: Observable<string>): void {
    this.instruments = datasetId$.switchMap(datasetId =>
      this.phenoBrowserService.getInstruments(datasetId)).share();
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

  search(value: string) {
    this.input$.next(value);
  }
}
