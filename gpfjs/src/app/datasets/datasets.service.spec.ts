import { TestBed, waitForAsync } from '@angular/core/testing';

import {
  HttpClient,
  HttpClientModule,
  HttpHandler,
  HttpHeaders,
} from '@angular/common/http';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { UsersService } from 'app/users/users.service';
import { RouterTestingModule } from '@angular/router/testing';
import { NgxsModule, StateStream, Store } from '@ngxs/store';
import { Dataset } from './datasets';
import { of } from 'rxjs/internal/observable/of';
import { environment } from 'environments/environment';
import { take } from 'rxjs/internal/operators/take';

describe('DatasetService', () => {
  let service: DatasetsService;
  beforeEach(waitForAsync(() => {
    const configMock = { 'baseUrl': 'testUrl/' };
    TestBed.configureTestingModule({
      imports: [NgxsModule.forRoot([]), RouterTestingModule, HttpClientTestingModule],
      providers: [
        DatasetsService,
        UsersService,
        {provide: ConfigService, useValue: configMock},
      ],
      declarations: [],
    }).compileComponents();

    service = TestBed.inject(DatasetsService);
  }));

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should fetch datasets', () => {
    const httpGetSpy = jest.spyOn(HttpClient.prototype, 'get');
    httpGetSpy.mockReturnValue(of('fakeResponse'));

    service.getDatasets().subscribe((post: Dataset[]) => {
      expect(httpGetSpy.mock.calls).toEqual([['testUrl/datasets', {withCredentials: true}]]);
    });
  });

  it('should get dataset', () => {
    const datasetFromJsonSpy = jest.spyOn(Dataset, 'fromDatasetAndDetailsJson');
    datasetFromJsonSpy.mockReturnValue('fakeDataset' as any);
    const httpGetSpy = jest.spyOn(HttpClient.prototype, 'get');
    httpGetSpy.mockReturnValue(of('fakeResponse'));

    service.getDataset('geneSymbol').pipe(take(1)).subscribe((response) => {
      expect(response).toEqual('fakeDataset' as any);
      expect(httpGetSpy.mock.calls[0][0]).toEqual('testUrl/datasets/geneSymbol');
      expect(httpGetSpy.mock.calls[1][0]).toEqual('testUrl/datasets/details/geneSymbol');
      expect(datasetFromJsonSpy.mock.calls).toEqual([[undefined, 'fakeResponse' as any]]);
    });
  });
});
