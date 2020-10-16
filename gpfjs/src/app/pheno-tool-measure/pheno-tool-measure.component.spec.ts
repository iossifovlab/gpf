import { HttpClient, HttpHandler } from '@angular/common/http';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';
import { MeasuresService } from 'app/measures/measures.service';
import { PhenoMeasureSelectorComponent } from 'app/pheno-measure-selector/pheno-measure-selector.component';
import { SearchableSelectComponent } from 'app/searchable-select/searchable-select.component';
import { StateRestoreService } from 'app/store/state-restore.service';
import { UsersService } from 'app/users/users.service';

import { PhenoToolMeasureComponent } from './pheno-tool-measure.component';

describe('PhenoToolMeasureComponent', () => {
  let component: PhenoToolMeasureComponent;
  let fixture: ComponentFixture<PhenoToolMeasureComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [
        PhenoToolMeasureComponent,
      ],
      providers: [
        StateRestoreService,
        MeasuresService,
        HttpClient,
        HttpHandler,
        ConfigService,
        DatasetsService,
        UsersService
      ],
      imports: [RouterTestingModule],
      schemas: [NO_ERRORS_SCHEMA]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PhenoToolMeasureComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
