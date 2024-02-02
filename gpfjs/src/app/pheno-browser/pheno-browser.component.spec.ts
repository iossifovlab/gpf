import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { PhenoBrowserComponent } from './pheno-browser.component';
import { DatasetsService } from '../datasets/datasets.service';
import { PhenoBrowserService } from './pheno-browser.service';
import { PhenoInstruments,PhenoInstrument, PhenoMeasures, PhenoMeasure, PhenoRegressions } from './pheno-browser';
import { fakeJsonMeasureOneRegression } from './pheno-browser.spec';
import { environment } from '../../environments/environment';
import { FormsModule } from '@angular/forms';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { GpfTableComponent } from '../table/table.component';
import { GpfTableCellComponent } from '../table/view/cell.component';
import { GpfTableEmptyCellComponent } from '../table/view/empty-cell.component';
import { GpfTableHeaderComponent } from '../table/view/header/header.component';
import { GpfTableHeaderCellComponent } from '../table/view/header/header-cell.component';
import { PhenoBrowserTableComponent } from '../pheno-browser-table/pheno-browser-table.component';
import { GpfTableColumnComponent } from '../table/component/column.component';
import { GpfTableContentHeaderComponent } from '../table/component/header.component';
import { GpfTableContentComponent } from '../table/component/content.component';
import { GpfTableCellContentDirective } from '../table/component/content.directive';
import { GpfTableSubcontentComponent } from '../table/component/subcontent.component';
import { GpfTableSubheaderComponent } from '../table/component/subheader.component';
import { NumberWithExpPipe } from '../utils/number-with-exp.pipe';
import { PValueIntensityPipe } from '../utils/p-value-intensity.pipe';
import { ActivatedRoute, Router } from '@angular/router';
import { Location } from '@angular/common';
import { BehaviorSubject, Observable, lastValueFrom, of, take } from 'rxjs';
import { ResizeService } from '../table/resize.service';
import { By } from '@angular/platform-browser';
import { ConfigService } from 'app/config/config.service';
import { RegressionComparePipe } from 'app/utils/regression-compare.pipe';
import { GetRegressionIdsPipe } from 'app/utils/get-regression-ids.pipe';
import { BackgroundColorPipe } from 'app/utils/background-color.pipe';
import { HttpClient, HttpHandler } from '@angular/common/http';

const fakeJsonMeasurei1 = JSON.parse(JSON.stringify(fakeJsonMeasureOneRegression)) as object;
fakeJsonMeasurei1['instrument_name'] = 'i1';
fakeJsonMeasurei1['measure_id'] = 'i1.test_measure';
fakeJsonMeasurei1['measure_name'] = 'test_measure';
(fakeJsonMeasurei1['regressions'] as PhenoRegressions[])[0]['measure_id']= 'i1.test_measure';

class MockPhenoBrowserService {
  public getInstruments(): Observable<PhenoInstruments> {
    return of(new PhenoInstruments('i1', ['i1', 'i2', 'i3']));
  }

  public getMeasures(): Observable<PhenoMeasure> {
    const measures = PhenoMeasure.fromJson(fakeJsonMeasurei1);
    return of(measures);
  }

  public getMeasuresInfo(): Observable<PhenoMeasures> {
    const measuresInfo = PhenoMeasures.fromJson(
      // eslint-disable-next-line @typescript-eslint/naming-convention
      {base_image_url: 'base', has_descriptions: true, regression_names: {age: 'age'}}
    );
    return of(measuresInfo);
  }

  public getDownloadLink(instrument: PhenoInstrument, datasetId: string): string {
    return `${environment.apiPath}pheno_browser/download`
           + `?dataset_id=${datasetId}&instrument=${instrument}`;
  }

  public validateMeasureDownload(): Observable<{status: number}> {
    return of({status: undefined});
  }

  public getDownloadMeasuresLink(): string {
    return '';
  }
}

class MockDatasetsService {
  public getSelectedDataset = (): object => ({accessRights: true, id: 'testDatasetId'});
  public getDatasetsLoadedObservable = (): Observable<void> => of();
}

class MockActivatedRoute {
  public params = {dataset: 'testDatasetId', get: (): string => ''};
  public parent = {params: of(this.params)};

  public queryParamMap = of(this.params);
}

class MockRouter {
  public createUrlTree(
    commands: unknown,
    navigationExtras: {
      queryParams: {
        instrument: string;
        search: string;
      };
    }): string {
    return `${navigationExtras.queryParams.instrument}/${navigationExtras.queryParams.search}`;
  }
}

const setQuery = (fixture: ComponentFixture<PhenoBrowserComponent>, instrument: number, search: string): void => {
  const selectElem = fixture.nativeElement.querySelector('select');
  const searchElem = fixture.nativeElement.querySelector('input');
  const selectedOptionElem = fixture.debugElement.queryAll(By.css('option'))[instrument];
  selectElem.value = selectedOptionElem.nativeElement.value;
  selectElem.dispatchEvent(new Event('change'));
  searchElem.value = search;
  searchElem.dispatchEvent(new Event('input'));
  fixture.detectChanges();
}

describe('PhenoBrowserComponent', () => {
  let component: PhenoBrowserComponent;
  let fixture: ComponentFixture<PhenoBrowserComponent>;
  let router;
  let location: Location;
  const activatedRoute = new MockActivatedRoute();
  const phenoBrowserServiceMock = new MockPhenoBrowserService();
  const datasetServiceMock = new MockDatasetsService();

  let locationSpy;
  const resizeSpy = {
    addResizeEventListener: jest.fn()
  };

  beforeEach(waitForAsync(() => {
    locationSpy = {
      replaceState: jest.fn()
    };

    TestBed.configureTestingModule({
      imports: [FormsModule, NgbModule],
      declarations: [GpfTableHeaderComponent, GpfTableHeaderCellComponent,
        GpfTableComponent, GpfTableCellComponent,
        GpfTableEmptyCellComponent, PhenoBrowserTableComponent,
        GpfTableColumnComponent, GpfTableContentComponent,
        GpfTableContentHeaderComponent, GpfTableSubcontentComponent,
        GpfTableSubheaderComponent, NumberWithExpPipe,
        PValueIntensityPipe, GpfTableCellContentDirective, RegressionComparePipe,
        PhenoBrowserComponent, GetRegressionIdsPipe, BackgroundColorPipe],
      providers: [
        PhenoBrowserComponent,
        HttpClient,
        HttpHandler,
        { provide: DatasetsService, useValue: datasetServiceMock },
        { provide: PhenoBrowserService, useValue: phenoBrowserServiceMock },
        { provide: ActivatedRoute, useValue: activatedRoute },
        { provide: Router, useClass: MockRouter },
        { provide: Location, useValue: locationSpy as object},
        { provide: PValueIntensityPipe, useClass: PValueIntensityPipe },
        { provide: ResizeService, useValue: resizeSpy },
        ConfigService
      ]
    }).compileComponents();

    router = TestBed.inject(Router);
    location = TestBed.inject(Location);

    fixture = TestBed.createComponent(PhenoBrowserComponent);
    component = fixture.componentInstance;

    component.ngOnInit();
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should list all instruments', waitForAsync(() => {
    const expectedInstruments = ['All instruments', 'i1', 'i2', 'i3'];
    const selectElemOptions = fixture.debugElement.queryAll(By.css('option'));

    const receivedInstruments = [];
    for (const option of selectElemOptions) {
      receivedInstruments.push((option.nativeElement as HTMLInputElement).textContent);
    }
    expect(receivedInstruments).toStrictEqual(expect.arrayContaining(expectedInstruments));
  }));

  it('should set the selected instrument to all instruments by default', async() => {
    await expect(lastValueFrom(component.selectedInstrument$.pipe(take(1)))).resolves.toBe('');
  });

  it('should set the selected instrument in the component correctly', async() => {
    setQuery(fixture, 2, '');
    await expect(lastValueFrom(component.selectedInstrument$.pipe(take(1)))).resolves.toBe('i2');
  });

  it('should pass search terms to the service correctly', waitForAsync(() => {
    jest.spyOn(phenoBrowserServiceMock, 'getMeasures');
    setQuery(fixture, 1, 'q10');
    fixture.whenStable().then(() => {
      expect(phenoBrowserServiceMock.getMeasures).toHaveBeenCalledTimes(2);
      expect(phenoBrowserServiceMock.getMeasures).toHaveBeenCalledWith('testDatasetId', 'i1', '');
      expect(phenoBrowserServiceMock.getMeasures).toHaveBeenCalledWith('testDatasetId', 'i1', 'q10');
    });
  }));

  it('should set the url with the selected instrument and search term', waitForAsync(() => {
    jest.spyOn(router, 'createUrlTree');
    setQuery(fixture, 2, 'q12');
    fixture.whenStable().then(() => {
      expect((router as Router).createUrlTree).toHaveBeenCalledTimes(2);
      expect((router as Router).createUrlTree).toHaveBeenCalledWith(['.'], {
        relativeTo: activatedRoute,
        queryParams: {instrument: 'i2', search: 'q12'}
      });
    });
  }));

  it('should set the selected instrument and search term from the url', waitForAsync(() => {
    setQuery(fixture, 3, 'q20');
    fixture.whenStable().then(() => {
      expect(location.replaceState).toHaveBeenCalledTimes(3);
      expect(location.replaceState).toHaveBeenCalledWith('i3/q20');
    });
  }));

  it('should test download', () => {
    const data = {
      /* eslint-disable @typescript-eslint/naming-convention */
      dataset_id: 'datasetId',
      instrument: 'instrument',
      search_term: 'search'
      /* eslint-enable */
    };
    component.selectedDatasetId = data.dataset_id;
    component.selectedInstrument$ = new BehaviorSubject(data.instrument);
    component.searchTermObs$ = of(data.search_term);

    const validateSpy = jest.spyOn(phenoBrowserServiceMock, 'validateMeasureDownload');
    const downloadSpy = jest.spyOn(phenoBrowserServiceMock, 'getDownloadMeasuresLink');

    validateSpy.mockReturnValue(of({ status: 404 }));
    component.downloadMeasures();
    expect(validateSpy).toHaveBeenCalledWith(data);
    expect(downloadSpy).not.toHaveBeenCalled();
    expect(component.errorModal).toBe(false);

    validateSpy.mockReturnValue(of({ status: 413 }));
    component.downloadMeasures();
    expect(validateSpy).toHaveBeenCalledWith(data);
    expect(downloadSpy).not.toHaveBeenCalled();
    expect(component.errorModal).toBe(true);

    component.errorModal = false;

    validateSpy.mockReturnValue(of({ status: 200 }));
    component.downloadMeasures();
    expect(validateSpy).toHaveBeenCalledWith(data);
    expect(downloadSpy).toHaveBeenCalledWith(data);
    expect(component.errorModal).toBe(false);
  });
});
