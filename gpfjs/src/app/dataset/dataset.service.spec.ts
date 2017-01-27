/* tslint:disable:no-unused-variable */
import { Injector } from '@angular/core';
import { TestBed, getTestBed, async, inject, fakeAsync, tick } from '@angular/core/testing';
import { DatasetService } from './dataset.service';
import { IdDescription } from '../common/iddescription';
import { IdName } from '../common/idname';
import { Phenotype } from '../phenotypes/phenotype';
import { Dataset } from '../dataset/dataset';
import { ConfigService } from '../config/config.service';

import {
  BaseRequestOptions, Http, HttpModule, XHRBackend,
  Response, ResponseOptions
} from '@angular/http';

import { MockBackend, MockConnection } from '@angular/http/testing/mock_backend';
import { Observable } from 'rxjs';

const mockDatasetsResponse: IdName[] =
  [
    {
      id: 'SD',
      name: 'Sequencing de Novo Dataset'
    },
    {
      id: 'SSC',
      name: 'SSC Description'
    },
    {
      id: 'VIP',
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
  let mockBackend: MockBackend;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      providers: [
        ConfigService,
        DatasetService,

        MockBackend,
        BaseRequestOptions,
        {
          provide: Http,
          deps: [MockBackend, BaseRequestOptions],
          useFactory:
          (backend: XHRBackend, defaultOptions: BaseRequestOptions) => {
            return new Http(backend, defaultOptions);
          }
        }
      ],
      imports: [
        HttpModule,
      ],

    });
    console.log('first before each called...');
    getTestBed().compileComponents();
    mockBackend = getTestBed().get(MockBackend);
  }));

  it('should parse correct response',
    async(inject([DatasetService], (service) => {
      console.log('test started...');

      mockBackend.connections.subscribe(
        (conn: MockConnection) => {
          console.log('connection url', conn.request.url);
          conn.mockRespond(
            new Response(
              new ResponseOptions(
                {
                  body: JSON.stringify({ data: mockDatasetsResponse })
                }
              )));
          console.log('mock response setup...');
        });

      service.getDatasets().subscribe(res => {
        expect(res.length).toBe(3);
        expect(res[0].id).toEqual('SD');
        expect(res[1].id).toEqual('SSC');
        expect(res[2].id).toEqual('VIP');
      });
    })
    ));


});

// describe('DatasetService', () => {
//  beforeEach(() => {
//    TestBed.configureTestingModule({
//      providers: [
//        ConfigService,
//        DatasetService,
//        MockBackend,
//        BaseRequestOptions,
//        {
//          provide: Http,
//          deps: [MockBackend, BaseRequestOptions],
//          useFactory: (backend, options) => { return new Http(backend, options); }
//        }]
//    });
//  });
//  it('should ...', inject([DatasetService], (service: DatasetService) => {
//    expect(service).toBeTruthy();
//  }));
//
//  it('should construct dataset service', async(inject(
//    [DatasetService, MockBackend], (service, mockBackend) => {
//
//      expect(service).toBeDefined();
//    }))
//  );
//
//
//
//  describe('getDatasets', () => {
//    it('should parse correct response', async(inject(
//      [DatasetService, MockBackend], (service, mockBackend) => {
//        console.log('async inject test started...');
//
//        mockBackend.connections.subscribe(conn => {
//          console.log('mocked response setup');
//          conn.mockRespond(
//            new Response(new ResponseOptions(
//              { body: JSON.stringify({ data: mockDatasetsResponse }) }
//            )));
//        });
//
//        const result: Observable<IdName[]> = service.getDatasets();
//
//        result.subscribe(res => {
//          expect(res.length).toEqual(2);
//        });
//      }))
//    );
//
//  });
// });
