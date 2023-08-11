import { TestBed } from '@angular/core/testing';

import { AppVersionService } from './app-version.service';
import { ConfigService } from './config/config.service';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { HttpClient } from '@angular/common/http';
import { lastValueFrom, of, take } from 'rxjs';
import { environment } from 'environments/environment';

describe('AppVersionService', () => {
  let service: AppVersionService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ConfigService],
      imports: [
        HttpClientTestingModule,
      ]
    });
    service = TestBed.inject(AppVersionService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should get gpf version', async() => {
    const httpGetSpy = jest.spyOn(HttpClient.prototype, 'get');
    httpGetSpy.mockReturnValue(of({ version: 'v1'}));

    const response = await lastValueFrom(service.getGpfVersion().pipe(take(1)));
    expect(httpGetSpy.mock.calls[0][0]).toStrictEqual(environment.apiPath + 'version');
    expect(response).toBe('v1');
  });
});
