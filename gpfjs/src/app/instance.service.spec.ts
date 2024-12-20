import { TestBed } from '@angular/core/testing';
import { ConfigService } from './config/config.service';
import { HttpClient, provideHttpClient } from '@angular/common/http';
import { lastValueFrom, of, take } from 'rxjs';
import { InstanceService } from './instance.service';
import { environment } from '../environments/environment';

describe('InstanceService', () => {
  let service: InstanceService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ConfigService, provideHttpClient()],
      imports: []
    });
    service = TestBed.inject(InstanceService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should get gpf version', async() => {
    const httpGetSpy = jest.spyOn(HttpClient.prototype, 'get');
    httpGetSpy.mockReturnValue(of({ version: 'v1'}));

    const response = await lastValueFrom(service.getGpfVersion().pipe(take(1)));
    expect(httpGetSpy.mock.calls[0][0]).toStrictEqual(environment.apiPath + 'instance/version');
    expect(response).toBe('v1');
  });
});
