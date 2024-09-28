import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { MeasuresService } from 'app/measures/measures.service';
import { PhenoMeasureSelectorComponent } from 'app/pheno-measure-selector/pheno-measure-selector.component';
import { UsersService } from 'app/users/users.service';
import { MultiContinuousFilterComponent } from './multi-continuous-filter.component';
import { Observable, of } from 'rxjs';
import { FormsModule } from '@angular/forms';
import { PhenoMeasure } from 'app/pheno-browser/pheno-browser';
import {
  MatAutocompleteOrigin,
  MatAutocomplete,
  MAT_AUTOCOMPLETE_SCROLL_STRATEGY,
  MatAutocompleteTrigger } from '@angular/material/autocomplete';
import { Store, StoreModule } from '@ngrx/store';
import { personFiltersReducer } from 'app/person-filters/person-filters.state';

const selectionMock = {
  isEmpty: (): boolean => true,
};

const ContinuousFilterStateMock = {
  id: '',
  type: '',
  role: '',
  from: '',
  source: '',
  sourceType: '',
  selection: selectionMock,
  isEmpty: (): boolean => true,
  min: 0,
  max: 0,
  domainMin: 0,
  domainMax: 0
};

const personFilterMock = {
  id: '',
  name: '',
  from: '',
  source: '',
  sourceType: '',
  role: '',
  filterType: '',
  domain: [''],
  // eslint-disable-next-line @typescript-eslint/no-empty-function, @typescript-eslint/explicit-function-return-type
  isEmpty: (): boolean => true,
  selection: selectionMock
};

class MockDatasetsService {
  public getSelectedDataset(): object {
    return { id: 'testDataset' };
  }
}

describe('MultiContinuousFilterComponent', () => {
  let component: MultiContinuousFilterComponent;
  let fixture: ComponentFixture<MultiContinuousFilterComponent>;
  const mockDatasetsService = new MockDatasetsService();
  let store: Store;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [
        MultiContinuousFilterComponent,
        PhenoMeasureSelectorComponent
      ],
      providers: [
        MultiContinuousFilterComponent,
        {provide: MeasuresService, useValue: {getContinuousMeasures: (): Observable<PhenoMeasure[]> => of()}},
        HttpClientTestingModule,
        ConfigService,
        {provide: DatasetsService, useValue: mockDatasetsService},
        UsersService,
        {provide: MAT_AUTOCOMPLETE_SCROLL_STRATEGY, useValue: ''}
      ],
      imports: [
        RouterTestingModule,
        StoreModule.forRoot({personFilters: personFiltersReducer}),
        FormsModule,
        MatAutocompleteOrigin,
        MatAutocomplete,
        MatAutocompleteTrigger
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(MultiContinuousFilterComponent);
    component = fixture.componentInstance;
    component.continuousFilter = personFilterMock;
    component.datasetId = '';
    component.continuousFilterState = ContinuousFilterStateMock;
    fixture.detectChanges();

    store = TestBed.inject(Store);

    jest.spyOn(store, 'select').mockReturnValue(of({
      familyFilters: [],
      personFilters: [],
    }));
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
