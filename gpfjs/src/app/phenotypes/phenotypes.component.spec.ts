/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { DebugElement } from '@angular/core';
import { Http } from '@angular/http';

import { PhenotypesComponent } from './phenotypes.component';
import { DatasetService, DatasetServiceInterface } from '../dataset/dataset.service';
import { IdDescription, Dataset, Phenotype } from '../dataset/dataset';

class DatasetServiceStub extends DatasetService implements DatasetServiceInterface {
  selectedDatasetId: string;
  getDatasets(): Promise<IdDescription[]> {
    return Promise.resolve([
      {
        id: 'ssc',
        description: 'SSC Description'
      },
      {
        id: 'vip',
        description: 'VIP Dataset'
      }
    ]);
  }

  getDataset(datasetId: string): Promise<Dataset> {
    return Promise.resolve({
      id: 'ssc',
      description: 'SSC Dataset',
      hasDenovo: true,
      hasTransmitted: true,
      hasCnv: true
    });
  }

  getPhenotypes(): Promise<Phenotype[]> {
    return Promise.resolve([
      {
        id: 'autism',
        description: 'autism',
        color: '#e35252'
      },
      {
        id: 'unaffected',
        description: 'unaffected',
        color: '#ffffff'
      }
    ]);
  }
}

let datasetService = new DatasetServiceStub(undefined);


describe('PhenotypesComponent', () => {
  let component: PhenotypesComponent;
  let fixture: ComponentFixture<PhenotypesComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [PhenotypesComponent],
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
