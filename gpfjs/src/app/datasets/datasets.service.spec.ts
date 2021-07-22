/* tslint:disable:no-unused-variable */
import { Injector } from '@angular/core';
import { TestBed, getTestBed, inject, fakeAsync, tick, waitForAsync } from '@angular/core/testing';
import { DatasetsService } from './datasets.service';
import { IdDescription } from '../common/iddescription';
import { IdName } from '../common/idname';
import { Dataset } from '../datasets/datasets';
import { ConfigService } from '../config/config.service';

// import {
//   BaseRequestOptions, XHRBackend, Response, ResponseOptions
// } from '@angular/http';

// import { MockBackend, MockConnection } from '@angular/http/testing/mock_backend';
import { Observable } from 'rxjs';


/*
const mockDatasetResponse: Dataset = {
  id: 'VIP',
  name: 'VIP Dataset',
  studies: ['VIP-JHC'],
  studyTypes: ['WE'],
  phenoDB: 'vip',

  genotypeBrowser: true,
  phenotypeTool: true,
  enrichmentTool: false,
  phenotypeBrowser: true,
  commonReport: true,

  genotypeBrowserConfig: {
    hasAdvancedFamilyFilters: false,
    hasPedigreeSelector: true,
    hasStudyTypes: false,
  },
  peopleGroups: [
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


export class DatasetsServiceStub {

  getDatasets(): Observable<Dataset[]> {
    return Observable.of([mockDatasetResponse]);
  }

  getDataset(datasetId: string): Observable<Dataset> {
    return Observable.of(mockDatasetResponse);
  }

  setSelectedDataset(dataset: Dataset): void {
    console.log('setSelectedDataset() called...');
    //    this.store.dispatch({
    //      'type': DATASETS_SELECT,
    //      'payload': dataset
    //
    //    });
    // this.selectedDataset.next(dataset);
  }


}

describe('DatasetService', () => {
  let mockBackend: MockBackend;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      providers: [
        ConfigService,
        DatasetsService,

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
    getTestBed().compileComponents();
    mockBackend = getTestBed().get(MockBackend);
  }));

  it('getDatasets() should parse correct response',
    async(inject([DatasetsService], (service) => {

      mockBackend.connections.subscribe(
        (conn: MockConnection) => {
          conn.mockRespond(
            new Response(
              new ResponseOptions(
                {
                  body: JSON.stringify({ data: [mockDatasetResponse] })
                }
              )));
        });

      service.getDatasets().subscribe(res => {
        expect(res.length).toBe(1);
        expect(res[0].id).toEqual('VIP');
      });
    })
    )
  );

  it('getDataset() should parse correct response',
    async(inject([DatasetsService], (service) => {

      mockBackend.connections.subscribe(
        (conn: MockConnection) => {
          conn.mockRespond(
            new Response(
              new ResponseOptions(
                {
                  body: JSON.stringify({ data: mockDatasetResponse })
                }
              )));
        });

      service.getDataset('VIP').subscribe(res => {
        expect(res.id).toEqual('VIP');
        expect(res.peopleGroups.length).toBe(2);
      });

    })
    )
  );



});

*/
