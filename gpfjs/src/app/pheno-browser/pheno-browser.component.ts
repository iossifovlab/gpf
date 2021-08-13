import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import { ActivatedRoute, Router, Params } from '@angular/router';
import { Location } from '@angular/common';

// tslint:disable-next-line:import-blacklist
import { Observable, BehaviorSubject, ReplaySubject, combineLatest, of } from 'rxjs';

import { PhenoBrowserService } from './pheno-browser.service';
import { PhenoInstruments, PhenoInstrument, PhenoMeasures, PhenoMeasure } from './pheno-browser';

import { Dataset } from 'app/datasets/datasets';
import { DatasetsService } from '../datasets/datasets.service';
import { debounceTime, distinctUntilChanged, map, share, switchMap, take, tap } from 'rxjs/operators';

@Component({
  selector: 'gpf-pheno-browser',
  templateUrl: './pheno-browser.component.html',
  styleUrls: ['./pheno-browser.component.css'],
})
export class PhenoBrowserComponent implements OnInit {
  public selectedInstrument$: BehaviorSubject<PhenoInstrument> = new BehaviorSubject<PhenoInstrument>(undefined);
  private measuresToShow: PhenoMeasures;
  public measuresToShow$: Observable<PhenoMeasures>;

  public instruments: Observable<PhenoInstruments>;
  public downloadLink$: Observable<string>;

  private selectedDatasetId: string;
  public selectedDataset$: Observable<Dataset>;

  public input$ = new ReplaySubject<string>(1);

  @ViewChild('searchBox') public searchBox: ElementRef;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private phenoBrowserService: PhenoBrowserService,
    private location: Location,
    private datasetsService: DatasetsService,
  ) { }

  public ngOnInit() {
    const datasetId$ = this.route.parent.params.pipe(
      take(1),
      map(params => <string>params['dataset'])
    );

    this.route.parent.params.subscribe((params: Params) => {
      this.selectedDatasetId = params['dataset'];
    });

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

    this.focusSearchBox();
  }

  private initMeasuresToShow(datasetId$: Observable<string>) {
    const searchTermObs$ = this.input$.pipe(
      map((searchTerm: string) => searchTerm.trim()),
      debounceTime(300),
      distinctUntilChanged()
    );

    this.measuresToShow$ = combineLatest([searchTermObs$, this.selectedInstrument$, datasetId$]).pipe(
      tap(([searchTerm, newSelection, datasetId]) => {
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
      }),
      switchMap(([searchTerm, newSelection, datasetId]) => {
        this.measuresToShow = null;
        return combineLatest([
            of(searchTerm),
            of(newSelection),
            of(datasetId),
            this.phenoBrowserService.getMeasuresInfo(datasetId)
        ]);
      }),
      switchMap(([searchTerm, newSelection, datasetId, measuresInfo]) => {
        this.measuresToShow = measuresInfo;
        return this.phenoBrowserService.getMeasures(datasetId, newSelection, searchTerm);
      }),
      map((measure: PhenoMeasure) => {
          if(this.measuresToShow === null) {
            return null;
          }
          this.measuresToShow._addMeasure(measure)
          return this.measuresToShow;
      }),
      share()
    );

    this.route.queryParamMap.pipe(
      map(params => [params.get('instrument') || '',  params.get('search') || '']),
      take(1)
    ).subscribe(([instrument, queryTerm]) => {
      this.search(queryTerm);
      this.emitInstrument(instrument);
    });
  }

  private initInstruments(datasetId$: Observable<string>): void {
    this.instruments = datasetId$.pipe(
      switchMap(datasetId => this.phenoBrowserService.getInstruments(datasetId)),
      share()
    );
  }

  public emitInstrument(instrument: PhenoInstrument) {
    this.selectedInstrument$.next(instrument);
  }

  private initDownloadLink(datasetId$: Observable<string>) {
    this.downloadLink$ = combineLatest([this.selectedInstrument$, datasetId$]).pipe(
      map(([instrument, datasetId]) =>
        this.phenoBrowserService.getDownloadLink(instrument, datasetId)
      )
    );
  }

  public search(value: string) {
    this.input$.next(value);
  }

  /**
  * Waits search box element to load.
  * @returns promise
  */
  private async waitForSearchBoxToLoad(): Promise<void> {
    return new Promise<void>(resolve => {
      const timer = setInterval(() => {
        if (this.searchBox !== undefined) {
          resolve();
          clearInterval(timer);
        }
      }, 200);
    });
  }

  private focusSearchBox(): void {
    this.waitForSearchBoxToLoad().then(() => {
      this.searchBox.nativeElement.focus();
    });
  }
}
