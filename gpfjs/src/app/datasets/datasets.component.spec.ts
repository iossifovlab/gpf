/* eslint-disable no-unused-vars, @typescript-eslint/no-unused-vars */
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DebugElement } from '@angular/core';

import { DatasetsComponent } from './datasets.component';
import { DatasetsService } from './datasets.service';
// import { DatasetsServiceStub } from '../datasets/datasets.service.spec';

// let datasetService = new DatasetsServiceStub();

xdescribe('DatasetComponent', () => {
  let component: DatasetsComponent;
  let fixture: ComponentFixture<DatasetsComponent>;

  beforeEach(async () => {
    TestBed.configureTestingModule({
      declarations: [DatasetsComponent],
      imports: [

      ],
      providers: [
        {
          // provide: DatasetsService,
          // useValue: datasetService
        }
      ]

    })
      .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(DatasetsComponent);
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