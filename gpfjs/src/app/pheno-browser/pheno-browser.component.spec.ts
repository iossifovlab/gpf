import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { PhenoBrowserComponent } from './pheno-browser.component';
import { PhenoBrowserService } from './pheno-browser.service';
import { PhenoInstruments, PhenoInstrument, PhenoMeasures } from './pheno-browser';
import { fakeJsonMeasure } from './pheno-browser.spec';
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
import { GpfTableCellContentDirective  } from '../table/component/content.directive';
import { GpfTableSubcontentComponent } from '../table/component/subcontent.component';
import { GpfTableSubheaderComponent } from '../table/component/subheader.component';
import { NumberWithExpPipe } from '../utils/number-with-exp.pipe';
import { PValueIntensityPipe } from '../utils/p-value-intensity.pipe';
import { ActivatedRoute, Router, Event } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { Location } from '@angular/common';
import { Observable, of } from 'rxjs';
import { ResizeService } from '../table/resize.service';
import { By } from '@angular/platform-browser';
import 'rxjs/add/operator/map';
import 'rxjs/add/operator/take';
import 'rxjs/add/operator/share';
import 'rxjs/add/operator/debounceTime';
import 'rxjs/add/operator/distinctUntilChanged';
import 'rxjs/add/operator/combineLatest';
import 'rxjs/add/operator/do';
import 'rxjs/add/operator/switchMap';
import 'rxjs/add/observable/combineLatest';
    

let fakeJsonMeasurei1 = JSON.parse(JSON.stringify(fakeJsonMeasure));
fakeJsonMeasurei1.instrument_name = 'i1';
fakeJsonMeasurei1.measure_id = 'i1.test_measure';


class MockPhenoBrowserService {
  getInstruments(datasetId: string): Observable<PhenoInstruments> {
    return of(new PhenoInstruments('i1', ['i1', 'i2', 'i3']));
  }

  getMeasures(datasetId: string, instrument: PhenoInstrument, search: string): Observable<PhenoMeasures> {
    let measures = PhenoMeasures.fromJson({'base_image_url': 'base', 'measures': [fakeJsonMeasurei1], 'has_descriptions': true});
    measures = PhenoMeasures.addBasePath(measures);
    return of(measures);
  }

  getDownloadLink(instrument: PhenoInstrument, datasetId: string) {
    return `${environment.apiPath}pheno_browser/download`
           + `?dataset_id=${datasetId}&instrument=${instrument}`
  }
}

class MockActivatedRoute {
  params = {dataset: 'testDatasetId', get: () => { return '' }};
  parent = {params: of(this.params)};

  queryParamMap = of(this.params);
}

class MockRouter {
  createUrlTree(commands: any[], navigationExtras: any) {
    return `${navigationExtras.queryParams.instrument}/${navigationExtras.queryParams.search}`;
  }
}

function setQuery(fixture: ComponentFixture<PhenoBrowserComponent>, instrument: number, search: string) {
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
  let router: MockRouter;
  let location: jasmine.SpyObj<Location>;
  let activatedRoute = new MockActivatedRoute();
  const phenoBrowserServiceMock = new MockPhenoBrowserService();

  let locationSpy: jasmine.SpyObj<Location>;
  const resizeSpy = jasmine.createSpyObj('ResizeService', ['addResizeEventListener']);

  beforeEach(async(() => { 
    locationSpy = jasmine.createSpyObj('Location', ['go']);

    TestBed.configureTestingModule({
      imports: [ FormsModule, NgbModule ],
      declarations: [ GpfTableHeaderComponent, GpfTableHeaderCellComponent, 
        GpfTableComponent, GpfTableCellComponent, 
        GpfTableEmptyCellComponent, PhenoBrowserTableComponent, 
        GpfTableColumnComponent, GpfTableContentComponent, 
        GpfTableContentHeaderComponent, GpfTableSubcontentComponent,
        GpfTableSubheaderComponent, NumberWithExpPipe,
        PValueIntensityPipe, GpfTableCellContentDirective,
        PhenoBrowserComponent ],
      providers: [
        PhenoBrowserComponent,
        { provide: PhenoBrowserService, useValue: phenoBrowserServiceMock },
        { provide: ActivatedRoute, useValue: activatedRoute },
        { provide: Router, useClass: MockRouter },
        { provide: Location, useValue: locationSpy },
        { provide: PValueIntensityPipe, useClass: PValueIntensityPipe },
        { provide: ResizeService, useValue: resizeSpy },
      ]
    })
    .compileComponents();

    router = TestBed.get(Router);
    location = TestBed.get(Location);
  
    fixture = TestBed.createComponent(PhenoBrowserComponent);
    component = fixture.componentInstance;

    component.ngOnInit();
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should list all instruments', async(() => {
    const expectedInstruments = ['All instruments', 'i1', 'i2', 'i3'];
    const selectElem = fixture.nativeElement.querySelector('select');
    const selectElemOptions = fixture.debugElement.queryAll(By.css('option'));

    let receivedInstruments = [];
    for (let option of selectElemOptions) {
      receivedInstruments.push(option.nativeElement.textContent);
    }
    expect(receivedInstruments).toEqual(jasmine.arrayContaining(expectedInstruments));
  }));

  it('should set the selected instrument to all instruments by default', async(() => {
    const selectElem = fixture.nativeElement.querySelector('select');
    fixture.whenStable().then(() => {
      component.selectedInstrument$.subscribe(
        value => expect(value).toEqual(''),
        fail
      );
    });
  }));

  it('should set the selected instrument in the component correctly', async(() => {
    setQuery(fixture, 2, '');
    fixture.whenStable().then(() => {
      component.selectedInstrument$.subscribe(
        value => expect(value).toEqual('i2'),
        fail
      );
    });
  }));

  it('should set the download link to the selected instrument', async(() => {
    const expectedDownloadLink = `${environment.apiPath}pheno_browser/download`
                                 + `?dataset_id=testDatasetId&instrument=i3`;
    setQuery(fixture, 3, '');
    fixture.whenStable().then(() => {
      component.downloadLink$.subscribe(
        value => expect(value).toEqual(expectedDownloadLink),
        fail
      );
    });
  }));

  it('should pass search terms to the service correctly', async(() => {
    spyOn(phenoBrowserServiceMock, 'getMeasures').and.callThrough();
    setQuery(fixture, 1, 'q10');
    fixture.whenStable().then(() => {
      expect(phenoBrowserServiceMock.getMeasures).toHaveBeenCalledTimes(2);
      expect(phenoBrowserServiceMock.getMeasures).toHaveBeenCalledWith('testDatasetId', 'i1', '');
      expect(phenoBrowserServiceMock.getMeasures).toHaveBeenCalledWith('testDatasetId', 'i1', 'q10');
    });
  }));

  it('should set the url with the selected instrument and search term', async(() => {
    spyOn(router, 'createUrlTree').and.callThrough();
    setQuery(fixture, 2, 'q12');
    fixture.whenStable().then(() => {
      expect(router.createUrlTree).toHaveBeenCalledTimes(2);
      expect(router.createUrlTree).toHaveBeenCalledWith(['.'], {
        relativeTo: activatedRoute,
        replaceUrl: true,
        queryParams: {instrument: 'i2', search: 'q12'}
      });
    });
  }));

  it('should set the selected instrument and search term from the url', async(() => {
    setQuery(fixture, 3, 'q20');
    fixture.whenStable().then(() => {
      // 2 (+1) calls since location is a jasmine spy obj
      expect(location.go).toHaveBeenCalledTimes(3);
      expect(location.go).toHaveBeenCalledWith('i3/q20');
    });
  }));

  it('should fetch and display all fields of a measure', async(() => {
    fixture.detectChanges();
    fixture.whenStable().then(() => {
      expect(fixture.nativeElement.textContent).toEqual(jasmine.stringMatching('i1'));
      expect(fixture.nativeElement.textContent).toEqual(jasmine.stringMatching('1.0e-6'));
      expect(fixture.nativeElement.textContent).toEqual(jasmine.stringMatching('0.2'));
      expect(fixture.nativeElement.textContent).toEqual(jasmine.stringMatching('0.3'));
      expect(fixture.nativeElement.textContent).toEqual(jasmine.stringMatching('0.4'));
      expect(fixture.nativeElement.textContent).toEqual(jasmine.stringMatching('test_measure'));
      expect(fixture.nativeElement.textContent).toEqual(jasmine.stringMatching('ordinal'));
      expect(fixture.nativeElement.textContent).toEqual(jasmine.stringMatching('a test measure'));
    });
  }));

  it('should color p values appropriately', async(() => {
    fixture.detectChanges();
    fixture.whenStable().then(() => {
      const lowPValueElement = fixture.debugElement.queryAll((dE) => dE.nativeElement.innerText == '1.0e-6')[0].children[0];
      const highPValueElement = fixture.debugElement.queryAll((dE) => dE.nativeElement.innerText == '0.20')[0].children[0];
      expect(lowPValueElement.nativeElement.style.backgroundColor).toEqual('rgba(255, 0, 0, 0.8)');
      expect(highPValueElement.nativeElement.style.backgroundColor).toEqual('rgba(255, 255, 255, 0.8)');
    });
  }));
  
});
