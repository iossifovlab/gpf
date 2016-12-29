/* tslint:disable:no-unused-variable */

import { TestBed, async, inject } from '@angular/core/testing';
import { DatasetService } from './dataset.service';
import { Dataset } from './dataset';

import {
  BaseRequestOptions, Http, HttpModule,
  Response, ResponseOptions
} from '@angular/http';

import { MockBackend } from '@angular/http/testing';
import { Observable } from 'rxjs';


describe('DatasetService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
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

  it('should construct', async(inject(
    [DatasetService, MockBackend], (service, mockBackend) => {

      expect(service).toBeDefined();
    })));

  describe('getDatasets', () => {
    const mockResponse: Dataset[] = [
      {
        id: 'ssc',
        description: 'SSC Dataset',
        has_denovo: true,
        has_transmitted: true,
        has_cnv: true,
        phenotypes: [
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
        ]
      }
    ];

    it('should parse response', async(inject(
      [DatasetService, MockBackend], (service, mockBackend) => {

        mockBackend.connections.subscribe(conn => {
          conn.mockRespond(
            new Response(new ResponseOptions(
              { body: JSON.stringify(mockResponse) }
            )));
        });

        const result: Observable<Dataset[]> = service.getDatasets();

        result.subscribe(res => {
          expect(res.length).toEqual(1);
        });
      })));

  });
});
