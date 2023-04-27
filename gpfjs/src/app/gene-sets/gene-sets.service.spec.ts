import { HttpClient } from '@angular/common/http';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
import { of } from 'rxjs';
import { GeneSetsService } from './gene-sets.service';
import { APP_BASE_HREF } from '@angular/common';

describe('GeneSetsService', () => {
  let service: GeneSetsService;

  beforeEach(() => {
    const configMock = { baseUrl: 'testUrl/' };
    TestBed.configureTestingModule({
      providers: [
        { provide: ConfigService, useValue: configMock },
        { provide: APP_BASE_HREF, useValue: '' },
        HttpClientTestingModule, GeneSetsService
      ],
      imports: [HttpClientTestingModule],
    });

    service = TestBed.inject(GeneSetsService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should getGeneSetsCollections', () => {
    const httpGetSpy = jest.spyOn(HttpClient.prototype, 'get');
    httpGetSpy.mockReturnValue(of('fakeResponse'));
    service.getGeneSetsCollections();

    expect(httpGetSpy.mock.calls).toEqual(
      [
        [
          'testUrl/gene_sets/gene_sets_collections',
          { headers: {'Content-Type': 'application/json'}, withCredentials: true }
        ]
      ]
    );
  });

  xit('should downloadGeneSet', () => {
    // TODO
  });
});
