import { HttpClient, HttpHandler } from '@angular/common/http';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NgxsModule } from '@ngxs/store';
import { ConfigService } from 'app/config/config.service';
import { MeasuresService } from 'app/measures/measures.service';
import { UsersService } from 'app/users/users.service';
import { APP_BASE_HREF } from '@angular/common';

import { PhenoToolMeasureComponent } from './pheno-tool-measure.component';
import { DatasetModel } from 'app/datasets/datasets.state';
import { of } from 'rxjs';
import { DatasetsService } from 'app/datasets/datasets.service';

describe('PhenoToolMeasureComponent', () => {
  let component: PhenoToolMeasureComponent;
  let fixture: ComponentFixture<PhenoToolMeasureComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [
        PhenoToolMeasureComponent,
      ],
      providers: [
        MeasuresService,
        HttpClient,
        HttpHandler,
        ConfigService,
        UsersService,
        DatasetsService,
        { provide: APP_BASE_HREF, useValue: '' }
      ],
      imports: [RouterTestingModule, NgxsModule.forRoot([], {developmentMode: true})],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    fixture = TestBed.createComponent(PhenoToolMeasureComponent);
    component = fixture.componentInstance;

    // eslint-disable-next-line max-len
    const selectedDatasetMockModel: DatasetModel = {selectedDatasetId: 'testId'};

    component['store'] = {
      selectOnce: () => of(selectedDatasetMockModel),
      dispatch: () => null
    } as never;

    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
