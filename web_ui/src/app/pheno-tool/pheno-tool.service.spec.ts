import { HttpClient, provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
import { of } from 'rxjs';
import { PhenoToolService } from './pheno-tool.service';
import { APP_BASE_HREF } from '@angular/common';

describe('PhenoToolService', () => {
  let service: PhenoToolService;

  beforeEach(() => {
    const configMock = { baseUrl: 'testUrl/' };
    TestBed.configureTestingModule({
      providers: [
        { provide: ConfigService, useValue: configMock },
        { provide: APP_BASE_HREF, useValue: '' },
        provideHttpClient(), provideHttpClientTesting(), PhenoToolService
      ],
      imports: [],
    });

    service = TestBed.inject(PhenoToolService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should get pheno tool results', () => {
    const httpGetSpy = jest.spyOn(HttpClient.prototype, 'post');
    httpGetSpy.mockReturnValue(of('fakeResponse'));
    service.getPhenoToolResults('filter' as any);

    expect(httpGetSpy.mock.calls).toStrictEqual(
      [
        [
          'testUrl/pheno_tool',
          'filter',
          {
            headers: {
              'Content-Type': 'application/json'
            },
            withCredentials: true
          }
        ]
      ]
    );
  });
});
