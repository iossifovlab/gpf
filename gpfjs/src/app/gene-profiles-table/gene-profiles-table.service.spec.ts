import { HttpClientTestingModule } from '@angular/common/http/testing';
import { fakeAsync, TestBed, tick } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
// eslint-disable-next-line no-restricted-imports
import { of } from 'rxjs';
import { GeneProfilesTableService } from './gene-profiles-table.service';
import { UsersService } from 'app/users/users.service';
import { APP_BASE_HREF } from '@angular/common';
import { StoreModule } from '@ngrx/store';

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
        { provide: APP_BASE_HREF, useValue: '' }
      ],
      imports: [HttpClientTestingModule, StoreModule.forRoot({})]
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
    expect(getUserGeneProfilesStateMock.mock.calls).toEqual([
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
    expect(saveUserGeneProfilesStateSpy.mock.calls).toEqual([]);

    tick(5000);
    expect(saveUserGeneProfilesStateSpy.mock.calls).toEqual([
      [service['config'].baseUrl + service['usersUrl'], state, {withCredentials: true}]
    ]);
  }));
});


