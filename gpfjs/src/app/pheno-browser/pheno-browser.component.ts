import { Component, OnInit, SimpleChanges, OnChanges } from '@angular/core';
import { ActivatedRoute, Router, Params } from '@angular/router';
import { Location } from '@angular/common';

// tslint:disable-next-line:import-blacklist
import { Observable, BehaviorSubject, ReplaySubject, combineLatest, of } from 'rxjs';

import { PhenoBrowserService } from './pheno-browser.service';
import { PhenoInstruments, PhenoInstrument, PhenoMeasures } from './pheno-browser';

import { Dataset } from 'app/datasets/datasets';
import { DatasetsService } from '../datasets/datasets.service';

@Component({
  selector: 'gpf-pheno-browser',
  templateUrl: './pheno-browser.component.html',
  styleUrls: ['./pheno-browser.component.css'],
})
export class PhenoBrowserComponent implements OnInit {

  selectedInstrument$: BehaviorSubject<PhenoInstrument> = new BehaviorSubject<PhenoInstrument>(undefined);
  private measuresToShow: PhenoMeasures;
  measuresToShow$: Observable<PhenoMeasures>;

  instruments: Observable<PhenoInstruments>;
  downloadLink$: Observable<string>;

  selectedDatasetId: string;
  selectedDataset$: Observable<Dataset>;

  input$ = new ReplaySubject<string>(1);

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private phenoBrowserService: PhenoBrowserService,
    private location: Location,
    private datasetsService: DatasetsService,
  ) { }

  ngOnInit() {
    const datasetId$ = this.route.parent.params
      .take(1)
      .map(params => <string>params['dataset']);

      this.route.parent.params.subscribe(
        (params: Params) => {
          this.selectedDatasetId = params['dataset'];
        }
      );

      this.selectedDataset$ = this.datasetsService.getSelectedDataset();

      this.selectedDataset$.subscribe(
        dataset => {
          if (dataset.accessRights) {
            this.initInstruments(datasetId$);
            this.initMeasuresToShow(datasetId$);
            this.initDownloadLink(datasetId$);
          }
        }
      );
  }

  initMeasuresToShow(datasetId$: Observable<string>) {
    this.measuresToShow$ = this.input$
      .map(searchTerm => searchTerm.trim())
      .debounceTime(300)
      .distinctUntilChanged()
      .combineLatest(this.selectedInstrument$, datasetId$)
      .do(([searchTerm, newSelection, datasetId]) => {
        this.measuresToShow = null;
        const queryParamsObject: any = {};
        if (newSelection) {
          queryParamsObject.instrument = newSelection;
        }
        if (searchTerm) {
          queryParamsObject.search = searchTerm;
        }
        const url = this.router.createUrlTree(['.'], { /* Removed unsupported properties by Angular migration: replaceUrl. */ relativeTo: this.route,
    queryParams: queryParamsObject }).toString();
        this.location.go(url);
      })
      .switchMap(([searchTerm, newSelection, datasetId]) => {
        this.measuresToShow = null;
        return combineLatest(
            of(searchTerm),
            of(newSelection),
            of(datasetId),
            this.phenoBrowserService.getMeasuresInfo(datasetId)
        );
      })
      .switchMap(([searchTerm, newSelection, datasetId, measuresInfo]) => {
        this.measuresToShow = measuresInfo;
        return this.phenoBrowserService.getMeasures(datasetId, newSelection, searchTerm);
      })
      .map(measure => {
          if(this.measuresToShow === null) {
            return null;
          }
          this.measuresToShow._addMeasure(measure)
          return this.measuresToShow;
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
