import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { Observable, of } from 'rxjs';
import { StudyFiltersComponent } from './study-filters.component';
import { NgbNavModule, NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { RemoveButtonComponent } from 'app/remove-button/remove-button.component';
import { AddButtonComponent } from 'app/add-button/add-button.component';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';
import { FormsModule } from '@angular/forms';
import { DatasetsComponent } from 'app/datasets/datasets.component';
import { UsersService } from 'app/users/users.service';
import { ConfigService } from 'app/config/config.service';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { APP_BASE_HREF } from '@angular/common';
import { DatasetsService } from 'app/datasets/datasets.service';
import { RouterModule } from '@angular/router';
import { DatasetNode } from 'app/dataset-node/dataset-node';
import { DatasetsTreeService } from 'app/datasets/datasets-tree.service';
import { Store, StoreModule } from '@ngrx/store';
import { studyTypesReducer } from 'app/study-types/study-types.state';
import { Dataset, GeneBrowser, PersonSet, PersonSetCollection, PersonSetCollections } from 'app/datasets/datasets';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { resetStudyFilters, setStudyFilters } from './study-filters.state';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const datasetConfigMock: any = {
  studies: ['test_name1', 'test_name2']
};

class DatasetsComponentMock {
  public datasets = {datasetTrees: [DatasetNode]};
}

const datasetMock = new Dataset(
  'id1',
  'name1',
  [],
  false,
  ['study1', 'study2'],
  ['studyName1', 'studyName2'],
  ['studyType1', 'studyType2'],
  'phenotypeData1',
  false,
  true,
  true,
  false,
  {enabled: true},
  null,
  new PersonSetCollections([
    new PersonSetCollection('collection1', 'nameCollection1',
      [
        new PersonSet('personSetId11', 'personSetName11', 'blue'),
        new PersonSet('personSetId12', 'personSetName12', 'blue'),
        new PersonSet('personSetId13', 'personSetName13', 'blue')
      ]
    ),
    new PersonSetCollection('collection2', 'nameCollection2',
      [
        new PersonSet('personSetId21', 'personSetName21', 'blue'),
        new PersonSet('personSetId22', 'personSetName22', 'blue'),
        new PersonSet('personSetId23', 'personSetName23', 'blue')
      ]
    )
  ]),
  null,
  new GeneBrowser(true, 'frequencyCol1', 'frequencyName1', 'effectCol1', 'locationCol1', 5, 6, true),
  false,
  true
);

const datasetMock2 = new Dataset(
  'id2',
  'name2',
  [],
  false,
  ['study1', 'study2'],
  ['studyName1', 'studyName2'],
  ['studyType1', 'studyType2'],
  'phenotypeData2',
  false,
  true,
  true,
  false,
  {enabled: true},
  null,
  null,
  null,
  new GeneBrowser(true, 'frequencyCol2', 'frequencyName2', 'effectCol2', 'locationCol2', 5, 6, true),
  false,
  true
);

class DatasetsServiceMock {
  public getDatasetsObservable(): Observable<Dataset[]> {
    return of([datasetMock, datasetMock2]);
  }
}

class MockDatasetsTreeService {
  public findNodeById(node: DatasetNode, id: string): DatasetNode | undefined {
    return node;
  }
}

describe('StudyFiltersComponent', () => {
  let component: StudyFiltersComponent;
  let fixture: ComponentFixture<StudyFiltersComponent>;
  let store: Store;
  const datasetsServiceMock = new DatasetsServiceMock();
  const datasetsTreeServiceMock = new MockDatasetsTreeService();


  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [
        StudyFiltersComponent,
        RemoveButtonComponent,
        AddButtonComponent,
        ErrorsAlertComponent
      ],
      providers: [
        NgbNavModule,
        NgbModule,
        FormsModule,
        UsersService,
        ConfigService,
        { provide: DatasetsTreeService, useValue: datasetsTreeServiceMock },
        { provide: DatasetsComponent, useValue: DatasetsComponentMock },
        { provide: DatasetsService, useValue: datasetsServiceMock },
        { provide: APP_BASE_HREF, useValue: '' },
        provideHttpClientTesting()
      ],
      imports: [
        NgbNavModule, NgbModule, FormsModule,
        StoreModule.forRoot({studyFilters: studyTypesReducer}),
        RouterModule.forRoot([])
      ],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();

    jest.clearAllMocks();
    jest.clearAllTimers();

    fixture = TestBed.createComponent(StudyFiltersComponent);
    component = fixture.componentInstance;

    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    store = TestBed.inject(Store);
    jest.spyOn(store, 'select').mockReturnValue(of(['studyFilter1', 'studyFilter2']));
    jest.spyOn(store, 'dispatch').mockReturnValue();

    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    component.dataset = datasetConfigMock;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should get root dataset of dataset tree', () => {
    component.ngOnInit();
    expect(component.rootDataset).toStrictEqual(new DatasetNode(
      datasetMock,
      [datasetMock, datasetMock2]
    ));
  });

  it('should get study filters from state', () => {
    const updateStateSpy = jest.spyOn(component, 'updateState');

    jest.useFakeTimers();
    const timer: ReturnType<typeof setTimeout> = setTimeout(() => '', 10);
    jest.spyOn(global, 'setTimeout').mockImplementation((fn) => {
      fn();
      return timer;
    });

    component.ngOnInit();
    jest.runAllTimers();

    expect(component.showStudyFilters).toBe(true);
    expect(updateStateSpy).toHaveBeenCalledWith(new Set(['studyFilter1', 'studyFilter2']));
  });

  it('should update state', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    component.updateState(new Set(['studyFilter1', 'studyFilter2']));
    expect(component.selectedStudies).toStrictEqual(new Set(['studyFilter1', 'studyFilter2']));
    expect(dispatchSpy).toHaveBeenCalledWith(setStudyFilters({ studyFilters: ['studyFilter1', 'studyFilter2'] }));
  });

  it('should reset selected studies when changing navigation tab', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    component.selectedStudies = new Set(['studyFilter1', 'studyFilter2']);

    component.onNavChange();
    expect(component.selectedStudies).toStrictEqual(new Set([]));
    expect(dispatchSpy).toHaveBeenCalledWith(resetStudyFilters());

    component.ngbNav.activeId = 'studies';
    component.selectedStudies = new Set(['studyFilter1', 'studyFilter2']);

    component.onNavChange();
    expect(component.selectedStudies).toStrictEqual(new Set(['studyFilter1', 'studyFilter2', '']));
  });
});
