import { HttpClientTestingModule } from '@angular/common/http/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { MeasuresService } from 'app/measures/measures.service';
import { UsersService } from 'app/users/users.service';

import { PhenoMeasureSelectorComponent } from './pheno-measure-selector.component';
import {
  MAT_AUTOCOMPLETE_SCROLL_STRATEGY,
  MatAutocomplete,
  MatAutocompleteOrigin,
  MatAutocompleteTrigger } from '@angular/material/autocomplete';
import { StoreModule } from '@ngrx/store';

class MockDatasetsService {
  public getSelectedDataset(): object {
    return { id: 'testDataset' };
  }
}

describe('PhenoMeasureSelectorComponent', () => {
  let component: PhenoMeasureSelectorComponent;
  let fixture: ComponentFixture<PhenoMeasureSelectorComponent>;
  const mockDatasetsService = new MockDatasetsService();

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [PhenoMeasureSelectorComponent],
      providers: [
        MeasuresService,
        ConfigService,
        {provide: DatasetsService, useValue: mockDatasetsService},
        UsersService,
        {provide: MAT_AUTOCOMPLETE_SCROLL_STRATEGY, useValue: ''}
      ],
      imports: [
        HttpClientTestingModule,
        RouterTestingModule,
        StoreModule.forRoot({}),
        MatAutocompleteOrigin,
        MatAutocomplete,
        MatAutocompleteTrigger],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    fixture = TestBed.createComponent(PhenoMeasureSelectorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
