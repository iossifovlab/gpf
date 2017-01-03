/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DebugElement } from '@angular/core';
import { Http } from '@angular/http';
import { MaterialModule } from '@angular/material';

import { PhenotypesComponent } from './phenotypes.component';
import { DatasetService, DatasetServiceInterface } from '../dataset/dataset.service';
import { IdDescription, Dataset, Phenotype } from '../dataset/dataset';

import { DatasetServiceStub } from '../dataset/dataset.service.spec';

let datasetService = new DatasetServiceStub(undefined);


describe('PhenotypesComponent', () => {
  let component: PhenotypesComponent;
  let fixture: ComponentFixture<PhenotypesComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [PhenotypesComponent],
      imports: [
        MaterialModule.forRoot()
      ],
      providers: [
        {
          provide: DatasetService,
          useValue: datasetService
        }
      ]

    })
      .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PhenotypesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
