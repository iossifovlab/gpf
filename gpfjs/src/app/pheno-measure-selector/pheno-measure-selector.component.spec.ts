import { HttpClientTestingModule } from '@angular/common/http/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { MeasuresService } from 'app/measures/measures.service';
import { SearchableSelectComponent } from 'app/searchable-select/searchable-select.component';
import { UsersService } from 'app/users/users.service';

import { PhenoMeasureSelectorComponent } from './pheno-measure-selector.component';

describe('PhenoMeasureSelectorComponent', () => {
  let component: PhenoMeasureSelectorComponent;
  let fixture: ComponentFixture<PhenoMeasureSelectorComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [PhenoMeasureSelectorComponent],
      providers: [MeasuresService, ConfigService, DatasetsService, UsersService, SearchableSelectComponent],
      imports: [HttpClientTestingModule, RouterTestingModule],
      schemas: [NO_ERRORS_SCHEMA]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PhenoMeasureSelectorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
