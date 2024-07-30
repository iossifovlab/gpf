import { Component, OnInit, ViewChild, ElementRef, OnDestroy, HostListener } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Location } from '@angular/common';
import { Observable, BehaviorSubject, ReplaySubject, combineLatest, of, zip, Subscription } from 'rxjs';
import { PhenoBrowserService } from './pheno-browser.service';
import { PhenoInstruments, PhenoInstrument, PhenoMeasures, PhenoMeasure } from './pheno-browser';
import { Dataset } from 'app/datasets/datasets';
import { debounceTime, distinctUntilChanged, map, share, switchMap, take, tap } from 'rxjs/operators';
import { environment } from 'environments/environment';
import { ConfigService } from 'app/config/config.service';
import { HttpClient } from '@angular/common/http';
import { Store } from '@ngxs/store';
import { DatasetModel } from 'app/datasets/datasets.state';
import { DatasetsService } from 'app/datasets/datasets.service';

@Component({
  selector: 'gpf-pheno-browser',
  templateUrl: './pheno-browser.component.html',
  styleUrls: ['./pheno-browser.component.css'],
})
export class PhenoBrowserComponent implements OnInit, OnDestroy {
  public selectedInstrument$: BehaviorSubject<PhenoInstrument> = new BehaviorSubject<PhenoInstrument>(undefined);
  public searchTermObs$: Observable<string>;
  public measuresToShow: PhenoMeasures;
  public measuresSubscription: Subscription;
  public errorModal = false;

  public instruments: Observable<PhenoInstruments>;
  public selectedDataset: Dataset;
  public input$ = new ReplaySubject<string>(1);
  @ViewChild('searchBox') public searchBox: ElementRef;
  public imgPathPrefix = environment.imgPathPrefix;

  private getPageSubscription: Subscription = new Subscription();
  private pageCount = 1;
  private allPagesLoaded = false;

  public constructor(
    private http: HttpClient,
    private route: ActivatedRoute,
    private router: Router,
    private phenoBrowserService: PhenoBrowserService,
    private location: Location,
    public configService: ConfigService,
    private store: Store,
    private datasetsService: DatasetsService
  ) { }

  public ngOnInit(): void {
    this.store.selectOnce((state: { datasetState: DatasetModel}) => state.datasetState).pipe(
      switchMap((state: DatasetModel) => this.datasetsService.getDataset(state.selectedDatasetId))
    ).subscribe(dataset => {
      if (!dataset) {
        return;
      }
      this.selectedDataset = dataset;

      this.initInstruments(this.selectedDataset.id);
      this.initMeasuresToShow(this.selectedDataset.id);
    });

    this.getPageSubscription?.unsubscribe();
    this.focusSearchBox();
  }

  private initMeasuresToShow(datasetId: string): void {
    this.searchTermObs$ = this.input$.pipe(
      map((searchTerm: string) => searchTerm.trim()),
      debounceTime(300),
      distinctUntilChanged()
    );

    this.measuresSubscription = combineLatest([this.searchTermObs$, this.selectedInstrument$]).pipe(
      tap(([searchTerm, newSelection]) => {
        this.measuresToShow = null;
        const queryParamsObject: {
            instrument: string;
            search: string;
        } = {
          instrument: undefined,
          search: undefined
        };
        if (newSelection) {
          queryParamsObject.instrument = newSelection;
        }
        if (searchTerm) {
          queryParamsObject.search = searchTerm;
        }
        const url = this.router.createUrlTree(['.'], {
          /* Removed unsupported properties by Angular migration: replaceUrl. */
          relativeTo: this.route,
          queryParams: queryParamsObject
        }).toString();
        this.location.replaceState(url);
      }),
      switchMap(([searchTerm, newSelection]) => {
        this.measuresToShow = null;
        return combineLatest([
          of(searchTerm),
          of(newSelection),
          this.phenoBrowserService.getMeasuresInfo(datasetId)
        ]);
      }),
      switchMap(([searchTerm, newSelection, measuresInfo]) => {
        this.measuresToShow = measuresInfo;
        return this.phenoBrowserService.getMeasures(this.pageCount, datasetId, newSelection, searchTerm);
      }),
      map((measures: PhenoMeasure[]) => {
        if (this.measuresToShow === null) {
          return null;
        }
        if (measures !== null) {
          measures.forEach(measure => {
            this.measuresToShow.addMeasure(measure);
          });
        }
        return this.measuresToShow;
      }),
      share()
    ).subscribe();

    this.route.queryParamMap.pipe(
      map(params => [params.get('instrument') || '', params.get('search') || '']),
      take(1)
    ).subscribe(([instrument, queryTerm]) => {
      this.search(queryTerm);
      this.emitInstrument(instrument);
    });
  }

  private initInstruments(datasetId: string): void {
    this.instruments = this.phenoBrowserService.getInstruments(datasetId);
  }

  public emitInstrument(instrument: PhenoInstrument): void {
    this.selectedInstrument$.next(instrument);
    this.pageCount = 1;
  }

  @HostListener('window:scroll', ['$event'])
  public updateTableOnScroll(): void {
    if (this.getPageSubscription.closed && window.scrollY + window.innerHeight + 200 > document.body.scrollHeight) {
      if (!this.allPagesLoaded) {
        this.pageCount++;
        this.updateTable();
      }
    }
  }

  private updateTable(orderBy?: string, sortBy?: string): void {
    this.getPageSubscription?.unsubscribe();
    this.getPageSubscription =
      this.phenoBrowserService.getMeasures(
        this.pageCount,
        this.selectedDataset.id,
        this.selectedInstrument$.value,
        (this.searchBox.nativeElement as HTMLInputElement).value,
        sortBy,
        orderBy
      ).subscribe(res => {
        if (!res.length) {
          this.allPagesLoaded = true;
          return;
        }

        res.forEach(r => {
          this.measuresToShow.addMeasure(r);
        });

        this.getPageSubscription.unsubscribe();
      });
  }

  public downloadMeasures(): void {
    combineLatest([this.searchTermObs$, this.selectedInstrument$])
      .pipe(
        take(1),
        switchMap(([searchTerm, instrument]) => {
          /* eslint-disable @typescript-eslint/naming-convention */
          const data = {
            dataset_id: this.selectedDataset.id,
            instrument: instrument,
            search_term: searchTerm
          };
          /* eslint-enable */
          return zip(
            of(data),
            this.phenoBrowserService.validateMeasureDownload(data)
          );
        })
      ).subscribe(([data, validity]) => {
        if (validity.status === 200) {
          // this.phenoBrowserService.getDownloadMeasuresLink(data)
          window.open(this.phenoBrowserService.getDownloadMeasuresLink(data));
        } else if (validity.status === 413) {
          this.errorModal = true;
        }
      });
  }

  public search(value: string): void {
    this.input$.next(value);
    this.pageCount = 1;
  }

  public handleSort(event: { id: string; order: string}): void {
    this.updateTable(event.order, event.id);
  }

  private async waitForSearchBoxToLoad(): Promise<void> {
    return new Promise<void>(resolve => {
      const timer = setInterval(() => {
        if (this.searchBox !== undefined) {
          resolve();
          clearInterval(timer);
        }
      }, 50);
    });
  }

  private focusSearchBox(): void {
    this.waitForSearchBoxToLoad().then(() => {
      (this.searchBox.nativeElement as HTMLInputElement).focus();
    });
  }

  public errorModalBack(): void {
    this.errorModal = false;
  }

  public ngOnDestroy(): void {
    this.measuresSubscription.unsubscribe();
    this.phenoBrowserService.cancelStreamPost();
  }
}
