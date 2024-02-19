import { HttpClientTestingModule} from '@angular/common/http/testing';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { UsersGroupsService } from 'app/users-groups/users-groups.service';
import { DatasetPermissions } from 'app/datasets-table/datasets-table';

import { GroupsTableComponent } from './groups-table.component';
import { UserGroup } from 'app/users-groups/users-groups';
import { Observable, lastValueFrom, of } from 'rxjs';
import { User } from 'app/users/users';
import { UsersService } from 'app/users/users.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { Item } from 'app/item-add-menu/item-add-menu';
import * as lodash from 'lodash';

const datasetMock1 = {datasetId: 'datasetId1', datasetName: 'dataset1'};
const datasetMock2 = {datasetId: 'datasetId2', datasetName: 'dataset2'};
const datasetMock3 = {datasetId: 'datasetId3', datasetName: 'dataset3'};
const datasetMock4 = {datasetId: 'datasetId4', datasetName: 'dataset4'};
const datasetMock5 = {datasetId: 'datasetId5', datasetName: 'dataset5'};
const datasetMock6 = {datasetId: 'datasetId6', datasetName: 'dataset6'};

const groupMock = new UserGroup(
  17,
  'fakeName',
  ['user1email', 'user2email', 'user3email', 'user4email'],
  [datasetMock1, datasetMock2, datasetMock3, datasetMock4, datasetMock5, datasetMock6]
);

class UsersGroupsServiceMock {
  public removeUser(): Observable<null> {
    return of(null);
  }

  public addUser(): Observable<null> {
    return of(null);
  }

  public revokePermissionToDataset(): Observable<null> {
    return of(null);
  }

  public grantPermissionToDataset(): Observable<null> {
    return of(null);
  }

  public getGroups(page: number, name: string): Observable<UserGroup[]> {
    const updatedGroup = lodash.cloneDeep(groupMock);
    updatedGroup.name = name;

    switch (name) {
      case 'removedUser':
        updatedGroup.users = ['user1email', 'user2email', 'user4email'];
        break;
      case 'addedUser':
        updatedGroup.users = updatedGroup.users.concat('newEmail');
        break;
      case 'removedDataset':
        updatedGroup.datasets = [datasetMock1, datasetMock2, datasetMock3, datasetMock5, datasetMock6];
        break;
      case 'addedDataset':
        updatedGroup.datasets = updatedGroup.datasets.concat({datasetId: 'datasetId7', datasetName: 'dataset7'});
        break;
      default:
        break;
    }
    return of([updatedGroup]);
  }
}

class UsersServiceMock {
  public getUsers(page: number): Observable<User[]> {
    let pageBody: User[];
    if (page === 1) {
      pageBody = [
        new User(1, 'user1', 'user1email', [], true, []),
        new User(2, 'user2', 'user2email', [], true, []),
        new User(3, 'user3', 'user3email', [], true, []),
        new User(4, 'user4', 'user4email', [], true, [])
      ];
    } else if (page === 2) {
      pageBody = [
        new User(5, 'user5', 'user5email', [], true, []),
        new User(6, 'user6', 'user6email', [], true, []),
        new User(7, 'user7', 'user7email', [], true, []),
        new User(8, 'user8', 'user8email', [], true, [])
      ];
    }
    return of(pageBody);
  }
}

class DatasetsServiceMock {
  public getManagementDatasets(page: number): Observable<DatasetPermissions[]> {
    let pageBody: DatasetPermissions[];
    if (page === 1) {
      pageBody = [
        new DatasetPermissions('1', 'dataset1', [], []),
        new DatasetPermissions('2', 'dataset2', [], []),
        new DatasetPermissions('3', 'dataset3', [], []),
        new DatasetPermissions('4', 'dataset4', [], [])
      ];
    } else if (page === 2) {
      pageBody = [
        new DatasetPermissions('5', 'dataset5', [], []),
        new DatasetPermissions('6', 'dataset6', [], []),
        new DatasetPermissions('7', 'dataset7', [], []),
        new DatasetPermissions('8', 'dataset8', [], []),
      ];
    }
    return of(pageBody);
  }
}

describe('GroupsTableComponent', () => {
  let component: GroupsTableComponent;
  let fixture: ComponentFixture<GroupsTableComponent>;
  const usersServiceMock = new UsersServiceMock();
  const usersGroupsServiceMock = new UsersGroupsServiceMock();
  const datasetsServiceMock = new DatasetsServiceMock();

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [
        GroupsTableComponent,
      ],
      providers: [
        { provide: UsersService, useValue: usersServiceMock },
        { provide: UsersGroupsService, useValue: usersGroupsServiceMock },
        { provide: DatasetsService, useValue: datasetsServiceMock }
      ],
      imports: [
        HttpClientTestingModule
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(GroupsTableComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should remove user from group', () => {
    const removeUserSpy = jest.spyOn(usersGroupsServiceMock, 'removeUser');
    const group = lodash.cloneDeep(groupMock);
    group.name = 'removedUser';

    component.removeUser(group, 'user3email');
    expect(removeUserSpy).toHaveBeenCalledWith('user3email', 'removedUser');
    expect(group).toStrictEqual(new UserGroup(
      groupMock.id,
      'removedUser',
      ['user1email', 'user2email', 'user4email'],
      groupMock.datasets
    ));
  });

  it('should add user to group', () => {
    const addUserSpy = jest.spyOn(usersGroupsServiceMock, 'addUser');
    const group = lodash.cloneDeep(groupMock);
    group.name = 'addedUser';

    component.addUser(group, new Item('user3', 'newEmail'));
    expect(addUserSpy).toHaveBeenCalledWith('newEmail', 'addedUser');
    expect(group).toStrictEqual(new UserGroup(
      groupMock.id,
      'addedUser',
      ['user1email', 'user2email', 'user3email', 'user4email', 'newEmail'],
      groupMock.datasets
    ));
  });

  it('should remove all users from group', () => {
    const getGroupsSpy = jest.spyOn(usersGroupsServiceMock, 'getGroups')
      .mockImplementation(() => of([] as UserGroup[]));
    const group = lodash.cloneDeep(groupMock);
    group.name = 'removedUsers';

    component.removeUser(group, 'user1email');
    expect(getGroupsSpy).toHaveBeenCalledWith(1, 'removedUsers');

    expect(group).toStrictEqual(new UserGroup(
      groupMock.id,
      'removedUsers',
      [],
      groupMock.datasets
    ));
    getGroupsSpy.mockRestore();
  });

  it('should remove dataset from group', () => {
    const revokePermissionToDatasetSpy = jest.spyOn(usersGroupsServiceMock, 'revokePermissionToDataset');
    const group = lodash.cloneDeep(groupMock);
    group.name = 'removedDataset';

    component.removeDataset(group, 'datasetId4');
    expect(revokePermissionToDatasetSpy).toHaveBeenCalledWith(groupMock.id, 'datasetId4');
    expect(group).toStrictEqual(new UserGroup(
      groupMock.id,
      'removedDataset',
      groupMock.users,
      [datasetMock1, datasetMock2, datasetMock3, datasetMock5, datasetMock6]
    ));
  });

  it('should add dataset to group', () => {
    const addDatasetSpy = jest.spyOn(usersGroupsServiceMock, 'grantPermissionToDataset');
    const group = lodash.cloneDeep(groupMock);
    group.name = 'addedDataset';

    component.addDataset(group, new Item('datasetId7', 'dataset7'));
    expect(addDatasetSpy).toHaveBeenCalledWith('addedDataset', 'datasetId7');
    expect(group).toStrictEqual(new UserGroup(
      groupMock.id,
      'addedDataset',
      groupMock.users,
      groupMock.datasets.concat({datasetId: 'datasetId7', datasetName: 'dataset7'}),
    ));
  });

  it('should remove all datasets from group', () => {
    const getGroupsSpy = jest.spyOn(usersGroupsServiceMock, 'getGroups')
      .mockImplementation(() => of([] as UserGroup[]));
    const group = lodash.cloneDeep(groupMock);
    group.name = 'removedDatasets';

    component.removeDataset(group, 'datasetId1');
    expect(getGroupsSpy).toHaveBeenCalledWith(1, 'removedDatasets');

    expect(group).toStrictEqual(new UserGroup(
      groupMock.id,
      'removedDatasets',
      groupMock.users,
      []
    ));
    getGroupsSpy.mockRestore();
  });

  it('should delete group', () => {
    const removeUserSpy = jest.spyOn(usersGroupsServiceMock, 'removeUser');
    const revokePermissionToDatasetSpy = jest.spyOn(usersGroupsServiceMock, 'revokePermissionToDataset');
    const groupToDelete = lodash.cloneDeep(groupMock);
    component.groups = [
      new UserGroup(1, 'group1', ['user1email'], [datasetMock1]),
      groupToDelete,
      new UserGroup(2, 'group2', ['user2email'], [datasetMock2])
    ];

    component.deleteGroup(groupToDelete);
    // eslint-ignore-next-line
    expect(removeUserSpy).toHaveBeenCalledWith('user1email', 'fakeName');
    expect(removeUserSpy).toHaveBeenCalledWith('user2email', 'fakeName');
    expect(removeUserSpy).toHaveBeenCalledWith('user3email', 'fakeName');
    expect(removeUserSpy).toHaveBeenCalledWith('user4email', 'fakeName');
    expect(revokePermissionToDatasetSpy).toHaveBeenCalledWith(17, 'datasetId1');
    expect(revokePermissionToDatasetSpy).toHaveBeenCalledWith(17, 'datasetId2');
    expect(revokePermissionToDatasetSpy).toHaveBeenCalledWith(17, 'datasetId3');
    expect(revokePermissionToDatasetSpy).toHaveBeenCalledWith(17, 'datasetId4');
    expect(revokePermissionToDatasetSpy).toHaveBeenCalledWith(17, 'datasetId5');
    expect(revokePermissionToDatasetSpy).toHaveBeenCalledWith(17, 'datasetId6');
    expect(component.groups).toStrictEqual([
      new UserGroup(1, 'group1', ['user1email'], [datasetMock1]),
      new UserGroup(2, 'group2', ['user2email'], [datasetMock2])
    ]);
  });

  it('should get user emails function', async() => {
    const getUsersSpy = jest.spyOn(usersServiceMock, 'getUsers');
    const group = lodash.cloneDeep(groupMock);
    group.users = ['user1email', 'user3email'];

    const getUsersLambda = component.getUserNamesFunction(group);

    let page = await lastValueFrom(getUsersLambda(1, 'search1'));
    expect(getUsersSpy).toHaveBeenCalledWith(1, 'search1');
    expect(page).toStrictEqual(
      [new Item('2', 'user2email'), new Item('4', 'user4email')]
    );

    page = await lastValueFrom(getUsersLambda(2, 'search2'));

    expect(getUsersSpy).toHaveBeenCalledWith(2, 'search2');
    expect(page).toStrictEqual(
      [
        new Item('5', 'user5email'),
        new Item('6', 'user6email'),
        new Item('7', 'user7email'),
        new Item('8', 'user8email')
      ]
    );
  });

  it('should get dataset names function', async() => {
    const getManagementDatasetsSpy = jest.spyOn(datasetsServiceMock, 'getManagementDatasets');
    const group = lodash.cloneDeep(groupMock);
    group.datasets = [{datasetId: 'datasetId2', datasetName: 'dataset2'}];

    const getDatasetNamesLambda = component.getDatasetNamesFunction(group);

    let page = await lastValueFrom(getDatasetNamesLambda(1, 'search1'));
    expect(getManagementDatasetsSpy).toHaveBeenCalledWith(1, 'search1');
    expect(page).toStrictEqual(
      [new Item('1', 'dataset1'), new Item('3', 'dataset3'), new Item('4', 'dataset4')]
    );

    page = await lastValueFrom(getDatasetNamesLambda(2, 'search2'));

    expect(getManagementDatasetsSpy).toHaveBeenCalledWith(2, 'search2');
    expect(page).toStrictEqual(
      [
        new Item('5', 'dataset5'),
        new Item('6', 'dataset6'),
        new Item('7', 'dataset7'),
        new Item('8', 'dataset8')
      ]
    );
  });
});
