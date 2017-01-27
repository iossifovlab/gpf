/* tslint:disable:no-unused-variable */

import { TestBed, async, inject } from '@angular/core/testing';
import { DatasetService } from './dataset.service';
import { IdDescription } from '../common/iddescription';
import { IdName } from '../common/idname';
import { Phenotype } from '../phenotypes/phenotype';
import { Dataset } from '../dataset/dataset';
import { ConfigService } from '../config/config.service';

import {
  BaseRequestOptions, Http, HttpModule,
  Response, ResponseOptions
} from '@angular/http';

import { MockBackend } from '@angular/http/testing';
import { Observable } from 'rxjs';

const mockDatasetsResponse: IdName[] =
  [
    {
      id: 'SD',
      name: 'Sequencing de Novo Dataset'
    },
    {
      id: 'ssc',
      name: 'SSC Description'
    },
    {
      id: 'vip',
      name: 'VIP Dataset'
    }
  ];

const mockDatasetResponse: Dataset = {
  id: 'VIP',
  name: 'VIP Dataset',
  studies: ['VIP-JHC'],
  studyTypes: ['WE'],
  phenoDB: 'vip',

  phenotypeGenotypeTool: true,
  enrichmentTool: false,
  phenotypeBrowser: true,

  genotypeBrowser: {
    hasDenovo: true,
    hasCNV: false,
    hasAdvancedFamilyFilters: false,
    hasTransmitted: true,
    hasPedigreeSelector: true,
    hasStudyTypes: false,
    mainForm: 'vip'
  },
  pedigreeSelectors: [
    {
      id: '16pstatus',
      name: '16p Status',
      source: 'phenoDB.pheno_common.genetic_status_16p',
      defaultValue: {
        color: '#aaaaaa',
        id: 'unknown',
        name: 'unknown'
      },
      domain: [
        {
          color: '#e35252',
          id: 'deletion',
          name: 'deletion'
        },
        {
          color: '#b8008a',
          id: 'duplication',
          name: 'duplication'
        },
        {
          color: '#e3d252',
          id: 'triplication',
          name: 'triplication'
        },
        {
          color: '#ffffff',
          id: 'negative',
          name: 'negative'
        }
      ]
    },
    {
      id: 'phenotypes',
      name: 'Phenotypes',
      source: 'legacy',
      defaultValue: {
        color: '#aaaaaa',
        id: 'unknown',
        name: 'unknown'
      },
      domain: [
        {
          color: '#e35252',
          id: 'autism',
          name: 'autism'
        },
        {
          color: '#ffffff',
          id: 'unaffected',
          name: 'unaffected'
        }
      ]
    }
  ]
};


export class DatasetServiceStub extends DatasetService {
  selectedDatasetId: string;
  getDatasets(): Observable<IdName[]> {
    return Observable.create(mockDatasetsResponse);
  }

  getDataset(datasetId: string): Observable<Dataset> {
    return Observable.create(mockDatasetResponse);
  }

}


describe('DatasetService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        ConfigService,
        DatasetService,
        MockBackend,
        BaseRequestOptions,
        {
          provide: Http,
          deps: [MockBackend, BaseRequestOptions],
          useFactory: (backend, options) => { return new Http(backend, options); }
        }]
    });
  });

  it('should ...', inject([DatasetService], (service: DatasetService) => {
    expect(service).toBeTruthy();
  }));

  it('should construct dataset service', async(inject(
    [DatasetService, MockBackend], (service, mockBackend) => {

      expect(service).toBeDefined();
    })));




});
