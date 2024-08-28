import { TestBed, waitForAsync } from '@angular/core/testing';

import { HttpClient } from '@angular/common/http';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { UsersService } from 'app/users/users.service';
import { RouterTestingModule } from '@angular/router/testing';
import { Dataset } from './datasets';
import { lastValueFrom, of, take } from 'rxjs';
import { APP_BASE_HREF } from '@angular/common';
import { StoreModule } from '@ngrx/store';

describe('DatasetService', () => {
  let service: DatasetsService;
  beforeEach(waitForAsync(() => {
    const configMock = { baseUrl: 'testUrl/' };
    TestBed.configureTestingModule({
      imports: [StoreModule.forRoot({}), RouterTestingModule, HttpClientTestingModule],
      providers: [
        DatasetsService,
        UsersService,
        {provide: ConfigService, useValue: configMock},
        { provide: APP_BASE_HREF, useValue: '' }
      ],
      declarations: [],
    }).compileComponents();
    jest.clearAllMocks();

    service = TestBed.inject(DatasetsService);
  }));

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should fetch datasets', async() => {
    const httpGetSpy = jest.spyOn(HttpClient.prototype, 'get');
    httpGetSpy.mockReturnValue(of('fakeResponse'));

    await lastValueFrom(service.getDatasets());
    // eslint-disable-next-line jest/prefer-strict-equal
    expect(httpGetSpy.mock.calls).toEqual([['testUrl/datasets', {withCredentials: true}]]);
  });

  it('should get dataset', async() => {
    const datasetFromJsonSpy = jest.spyOn(Dataset, 'fromDatasetAndDetailsJson');
    datasetFromJsonSpy.mockReturnValue('fakeDataset' as any);
    const httpGetSpy = jest.spyOn(HttpClient.prototype, 'get');
    httpGetSpy.mockReturnValue(of('fakeResponse'));

    const response = await lastValueFrom(service.getDataset('geneSymbol').pipe(take(1)));
    expect(response).toBe('fakeDataset' as any);
    expect(httpGetSpy.mock.calls[0][0]).toBe('testUrl/datasets/geneSymbol');
    expect(httpGetSpy.mock.calls[1][0]).toBe('testUrl/datasets/details/geneSymbol');
    // eslint-disable-next-line jest/prefer-strict-equal
    expect(datasetFromJsonSpy.mock.calls).toEqual([[undefined, 'fakeResponse' as any]]);
  });
});
