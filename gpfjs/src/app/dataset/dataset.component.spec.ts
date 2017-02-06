/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DebugElement } from '@angular/core';

import { DatasetComponent } from './dataset.component';
import { DatasetService } from './dataset.service';
import { DatasetServiceStub } from '../dataset/dataset.service.spec';


import { gpfReducer } from '../store/gpf-store';
import { StoreModule } from '@ngrx/store';

let datasetService = new DatasetServiceStub();


describe('DatasetComponent', () => {
  let component: DatasetComponent;
  let fixture: ComponentFixture<DatasetComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [DatasetComponent],
      imports: [
        StoreModule.provideStore(gpfReducer),
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
    fixture = TestBed.createComponent(DatasetComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('check for selectedDataset', () => {

    expect(component.selectedDataset.id).toEqual('VIP');

  });
});
