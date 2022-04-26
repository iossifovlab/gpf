import { HttpClient, HttpHandler } from '@angular/common/http';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NgxsModule } from '@ngxs/store';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { MeasuresService } from 'app/measures/measures.service';
import { UsersService } from 'app/users/users.service';

import { PhenoToolMeasureComponent } from './pheno-tool-measure.component';

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
        DatasetsService,
        UsersService
      ],
      imports: [RouterTestingModule, NgxsModule.forRoot([], {developmentMode: true})],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();
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
