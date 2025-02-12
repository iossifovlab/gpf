import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
import { UsersGroupsService } from './users-groups.service';
import { HttpClient, provideHttpClient } from '@angular/common/http';
import { of, lastValueFrom, take } from 'rxjs';
import { UserGroup } from './users-groups';

const datasetMock1 = {
  datasetName: 'datasetName',
  datasetId: 'datasetId1',
};

const datasetMock2 = {
  datasetName: 'datasetName',
  datasetId: 'datasetId2',
};

const groupsMockObj = [
  { id: 1, name: 'group1', users: [], datasets: [datasetMock1, datasetMock2]},
  { id: 2, name: 'group2', users: [], datasets: [] },
];

describe('UsersGroupsService', () => {
  let service: UsersGroupsService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [UsersGroupsService, ConfigService, provideHttpClient(), provideHttpClientTesting()],
      imports: []
    });

    service = TestBed.inject(UsersGroupsService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should get all groups', async() => {
    const groupsMock = [
      { id: 1, name: 'group1', users: [], datasets: []},
      { id: 2, name: 'group2', users: [], datasets: [] },
    ];

    const groupsMockRes = [
      new UserGroup(1, 'group1', [], []),
      new UserGroup(2, 'group2', [], []),
    ];
    const httpGetSpy = jest.spyOn(HttpClient.prototype, 'get');
    httpGetSpy.mockReturnValue(of(groupsMock));

    const getResponse = service.getAllGroups();

    expect(httpGetSpy).toHaveBeenCalledWith(
      service['config'].baseUrl + service['groupsUrl'],
      { withCredentials: true }
    );
    const res = await lastValueFrom(getResponse.pipe(take(1)));
    expect(res).toStrictEqual(groupsMockRes);
  });

  it('should get groups by search', async() => {
    const groupsMockRes = [
      new UserGroup(1, 'group1', [], [
        {datasetId: 'datasetId1', datasetName: 'datasetName(datasetId1)'},
        {datasetId: 'datasetId2', datasetName: 'datasetName(datasetId2)'},
      ]),
      new UserGroup(2, 'group2', [], []),
    ];
    const url = service['config'].baseUrl + service['groupsUrl'] + '?page=1&search=searchValue';

    const httpGetSpy = jest.spyOn(HttpClient.prototype, 'get');
    httpGetSpy.mockReturnValue(of(groupsMockObj));

    const getResponse = service.getGroups(1, 'searchValue');
    expect(httpGetSpy).toHaveBeenCalledWith(
      url,
      { withCredentials: true }
    );
    const res = await lastValueFrom(getResponse.pipe(take(1)));
    expect(res).toStrictEqual(groupsMockRes);
  });

  it('should get invalid response when getting groups', async() => {
    const url = service['config'].baseUrl + service['groupsUrl'] + '?page=1&search=searchValue';

    const httpGetSpy = jest.spyOn(HttpClient.prototype, 'get');
    httpGetSpy.mockReturnValue(of(null));

    const getResponse = service.getGroups(1, 'searchValue');
    expect(httpGetSpy).toHaveBeenCalledWith(
      url,
      { withCredentials: true }
    );
    const res = await lastValueFrom(getResponse.pipe(take(1)));
    expect(res).toStrictEqual([]);
  });

  it('should get group by name', async() => {
    const groupObj = { id: 1, name: 'group1', users: [], datasets: [] };
    const groupRes = new UserGroup(1, 'group1', [], []);
    const httpGetSpy = jest.spyOn(HttpClient.prototype, 'get');
    httpGetSpy.mockReturnValue(of(groupObj));

    const getResponse = service.getGroup('group1');
    expect(httpGetSpy).toHaveBeenCalledWith(
      service['config'].baseUrl + service['groupsUrl'] + '/group1',
      { withCredentials: true }
    );
    const res = await lastValueFrom(getResponse.pipe(take(1)));
    expect(res).toStrictEqual(groupRes);
  });

  it('should get permission to dataset', async() => {
    const httpPostSpy = jest.spyOn(HttpClient.prototype, 'post');
    httpPostSpy.mockReturnValue(of(null));

    const postResponse = service.grantPermissionToDataset('group2', 'datasetId1');

    expect(httpPostSpy).toHaveBeenCalledWith(
      service['config'].baseUrl + service['groupGrantPermissionUrl'],
      { groupName: 'group2', datasetId: 'datasetId1' },
      { withCredentials: true }
    );
    const res = await lastValueFrom(postResponse.pipe(take(1)));
    expect(res).toBeNull();
  });

  it('should revoke permission to dataset', async() => {
    const httpPostSpy = jest.spyOn(HttpClient.prototype, 'post');
    httpPostSpy.mockReturnValue(of(null));

    const postResponse = service.revokePermissionToDataset(2, 'datasetId1');

    expect(httpPostSpy).toHaveBeenCalledWith(
      service['config'].baseUrl + service['groupRevokePermissionUrl'],
      { groupId: 2, datasetId: 'datasetId1' },
      { withCredentials: true }
    );
    const res = await lastValueFrom(postResponse.pipe(take(1)));
    expect(res).toBeNull();
  });

  it('should add user to a group', async() => {
    const httpPostSpy = jest.spyOn(HttpClient.prototype, 'post');
    httpPostSpy.mockReturnValue(of(null));

    const postResponse = service.addUser('user@email.com', 'group2');

    expect(httpPostSpy).toHaveBeenCalledWith(
      service['config'].baseUrl + service['groupsUrl'] + '/add-user',
      { userEmail: 'user@email.com', groupName: 'group2' },
      { withCredentials: true }
    );
    const res = await lastValueFrom(postResponse.pipe(take(1)));
    expect(res).toBeNull();
  });

  it('should remove user from a group', async() => {
    const httpPostSpy = jest.spyOn(HttpClient.prototype, 'post');
    httpPostSpy.mockReturnValue(of(null));

    const postResponse = service.removeUser('user@email.com', 'group2');

    expect(httpPostSpy).toHaveBeenCalledWith(
      service['config'].baseUrl + service['groupsUrl'] + '/remove-user',
      { userEmail: 'user@email.com', groupName: 'group2' },
      { withCredentials: true }
    );
    const res = await lastValueFrom(postResponse.pipe(take(1)));
    expect(res).toBeNull();
  });
});
