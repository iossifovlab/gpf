/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DebugElement } from '@angular/core';

import { PedigreeSelectorComponent } from './pedigree-selector.component';

import { Dataset } from '../dataset/dataset';
import { DatasetService } from '../dataset/dataset.service';
import { DatasetServiceStub } from '../dataset/dataset.service.spec';

let datasetService = new DatasetServiceStub(undefined, undefined);

describe('PedigreeselectorComponent', () => {
  let component: PedigreeSelectorComponent;
  let fixture: ComponentFixture<PedigreeSelectorComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [PedigreeSelectorComponent],
      imports: [
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
    fixture = TestBed.createComponent(PedigreeSelectorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
