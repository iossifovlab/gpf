import { provideHttpClientTesting } from '@angular/common/http/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { MeasuresService } from 'app/measures/measures.service';
import { UsersService } from 'app/users/users.service';

import {
  MAT_AUTOCOMPLETE_SCROLL_STRATEGY,
  MatAutocomplete,
  MatAutocompleteOrigin,
  MatAutocompleteTrigger } from '@angular/material/autocomplete';
import { StoreModule } from '@ngrx/store';
import { Measure } from 'app/measures/measures';
import { of } from 'rxjs';
import { PhenoMeasureSelectorBetaComponent } from './pheno-measure-selector-beta.component';

class MockDatasetsService {
  public getSelectedDataset(): object {
    return { id: 'testDataset' };
  }
}

const mockMeasures = [
  new Measure('m1', 'desc1'),
  new Measure('m2', 'desc2'),
  new Measure('m3', 'desc3'),
  new Measure('m4', 'desc4'),
];

class MockMeasuresService {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  public getMeasureList(datasetId: string): object {
    return of(mockMeasures);
  }
}

describe('PhenoMeasureSelectorBetaComponent', () => {
  let component: PhenoMeasureSelectorBetaComponent;
  let fixture: ComponentFixture<PhenoMeasureSelectorBetaComponent>;
  const mockDatasetsService = new MockDatasetsService();
  const mockMeasuresService = new MockMeasuresService();

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [PhenoMeasureSelectorBetaComponent],
      providers: [
        MeasuresService,
        {provide: MeasuresService, useValue: mockMeasuresService},
        ConfigService,
        {provide: DatasetsService, useValue: mockDatasetsService},
        UsersService,
        {provide: MAT_AUTOCOMPLETE_SCROLL_STRATEGY, useValue: ''},
        provideHttpClientTesting()
      ],
      imports: [
        RouterTestingModule,
        StoreModule.forRoot({}),
        MatAutocompleteOrigin,
        MatAutocomplete,
        MatAutocompleteTrigger],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    fixture = TestBed.createComponent(PhenoMeasureSelectorBetaComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
