import { provideHttpClientTesting } from '@angular/common/http/testing';
import { fakeAsync, TestBed, tick } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
import { of } from 'rxjs';
import { GeneProfilesTableService } from './gene-profiles-table.service';
import { UsersService } from 'app/users/users.service';
import { APP_BASE_HREF } from '@angular/common';
import { StoreModule } from '@ngrx/store';
import { provideHttpClient } from '@angular/common/http';

class UsersServiceMock {
  public cachedUserInfo(): object {
    return {loggedIn: true};
  }
}

describe('GeneProfilesTableService', () => {
  let service: GeneProfilesTableService;
  const usersServiceMock = new UsersServiceMock();

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ConfigService,
        { provide: UsersService, useValue: usersServiceMock},
        { provide: APP_BASE_HREF, useValue: '' },
        provideHttpClient(),
        provideHttpClientTesting()
      ],
      imports: [StoreModule.forRoot({})]
    });
    service = TestBed.inject(GeneProfilesTableService);

    service['store'] = {
      select: () => of({
        headerLeaves: [],
        higlightedRows: ['CHD8'],
        openedTabs: ['POGZ'],
        orderBy: '',
        searchValue: 'chd',
        sortBy: '' })
    } as never;
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should get genes', () => {
    const getGenesSpy = jest.spyOn(service['http'], 'get');

    getGenesSpy.mockReturnValue(of({}));
    service.getGenes(1);
    service.getGenes(1, 'mockSearch');
    service.getGenes(1, 'mockSearch', 'mockSort', 'desc');
    expect(getGenesSpy.mock.calls).toEqual([ // eslint-disable-line
      [service['config'].baseUrl + service['genesUrl'] + '?page=1'],
      [service['config'].baseUrl + service['genesUrl'] + '?page=1&symbol=mockSearch'],
      [service['config'].baseUrl + service['genesUrl'] + '?page=1&symbol=mockSearch&sortBy=mockSort&order=desc']
    ]);
  });

  it('should get user gene profiles state', () => {
    const getUserGeneProfilesStateMock = jest.spyOn(service['http'], 'get').mockReturnValue(
      {
        headerLeaves: [],
        higlightedRows: ['CHD8'],
        openedTabs: ['POGZ'],
        orderBy: '',
        searchValue: 'chd',
        sortBy: '' } as never
    );

    const res$ = service.getUserGeneProfilesState();
    expect(getUserGeneProfilesStateMock.mock.calls).toStrictEqual([
      [service['config'].baseUrl + service['usersUrl'], {withCredentials: true}]
    ]);

    expect(res$).toStrictEqual({
      headerLeaves: [],
      higlightedRows: ['CHD8'],
      openedTabs: ['POGZ'],
      orderBy: '',
      searchValue: 'chd',
      sortBy: '' });
  });

  it('should save user gene profiles state', fakeAsync(() => {
    const saveUserGeneProfilesStateSpy = jest.spyOn(service['http'], 'post');
    const state = {
      headerLeaves: [],
      higlightedRows: ['CHD8'],
      openedTabs: ['POGZ'],
      orderBy: '',
      searchValue: 'chd',
      sortBy: '' };

    service.saveUserGeneProfilesState(); // Expected to be cancelled
    service.saveUserGeneProfilesState(); // Expected to cancel the first one
    expect(saveUserGeneProfilesStateSpy.mock.calls).toStrictEqual([]);

    tick(5000);
    expect(saveUserGeneProfilesStateSpy.mock.calls).toStrictEqual([
      [service['config'].baseUrl + service['usersUrl'], state, {withCredentials: true}]
    ]);
  }));

  describe('pagehide flushing', () => {
    let originalSendBeacon: typeof navigator.sendBeacon | undefined;
    let sendBeaconMock: jest.Mock;

    beforeEach(() => {
      originalSendBeacon = navigator.sendBeacon;
      sendBeaconMock = jest.fn().mockReturnValue(true);
      Object.defineProperty(navigator, 'sendBeacon', {
        value: sendBeaconMock,
        configurable: true,
        writable: true,
      });
    });

    afterEach(() => {
      service.ngOnDestroy();
      Object.defineProperty(navigator, 'sendBeacon', {
        value: originalSendBeacon,
        configurable: true,
        writable: true,
      });
    });

    it('should flush a pending save via sendBeacon on pagehide', fakeAsync(() => {
      service.saveUserGeneProfilesState();

      window.dispatchEvent(new Event('pagehide'));

      expect(sendBeaconMock).toHaveBeenCalledTimes(1);
      const [url, body] = sendBeaconMock.mock.calls[0] as [string, Blob];
      expect(url).toBe(service['config'].baseUrl + service['usersUrl']);
      expect(body).toBeInstanceOf(Blob);
      expect(body.type).toBe('application/json');

      // Drain any pending timers so fakeAsync doesn't complain.
      tick(5000);
    }));

    it('should not call sendBeacon on pagehide after the trailing save has already fired',
      fakeAsync(() => {
        // Drain the debounce so the trailing-edge POST fires and clears the timer.
        service.saveUserGeneProfilesState();
        tick(2000);

        window.dispatchEvent(new Event('pagehide'));
        expect(sendBeaconMock).not.toHaveBeenCalled();
      }));

    it('should cancel the pending HTTP POST after a pagehide flush', fakeAsync(() => {
      const httpPostSpy = jest.spyOn(service['http'], 'post');

      service.saveUserGeneProfilesState();
      window.dispatchEvent(new Event('pagehide'));
      expect(sendBeaconMock).toHaveBeenCalledTimes(1);

      tick(5000);
      expect(httpPostSpy).not.toHaveBeenCalled();
    }));

    it('should not call sendBeacon on pagehide if the user has logged out', fakeAsync(() => {
      service.saveUserGeneProfilesState();

      const userSpy = jest.spyOn(usersServiceMock, 'cachedUserInfo')
        .mockReturnValue({loggedIn: false});
      try {
        window.dispatchEvent(new Event('pagehide'));
        expect(sendBeaconMock).not.toHaveBeenCalled();
        tick(5000);
      } finally {
        userSpy.mockRestore();
      }
    }));

    it('should not flush twice when the listener is invoked twice', fakeAsync(() => {
      service.saveUserGeneProfilesState();

      window.dispatchEvent(new Event('pagehide'));
      window.dispatchEvent(new Event('pagehide'));

      expect(sendBeaconMock).toHaveBeenCalledTimes(1);
      tick(5000);
    }));
  });
});


