import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { DatasetsService } from 'app/datasets/datasets.service';
import { UsersGroupsService } from 'app/users-groups/users-groups.service';
import { DatasetsTableComponent } from './datasets-table.component';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { Observable, lastValueFrom, of } from 'rxjs';
import { DatasetPermissions } from './datasets-table';
import * as lodash from 'lodash';
import { UserGroup } from 'app/users-groups/users-groups';
import { Item } from 'app/item-add-menu/item-add-menu';
import { StoreModule } from '@ngrx/store';

const datasetMock = new DatasetPermissions(
  'datasetId',
  'datasetName',
  ['group1', 'group2', 'group3'],
  [
    {name: 'user1', email: 'user1email'},
    {name: 'user2', email: 'user2email'},
    {name: 'user3', email: 'user3email'}
  ]
);

const datasetInDB = lodash.cloneDeep(datasetMock);

class UsersGroupsServiceMock {
  public getGroup(groupName: string): Observable<UserGroup> {
    return of(new UserGroup(1, groupName, [], []));
  }

  public getGroups(page: number): Observable<UserGroup[]> {
    let pageBody: UserGroup[];
    if (page === 1) {
      pageBody = [
        new UserGroup(1, 'group1', [], []),
        new UserGroup(2, 'group2', [], []),
        new UserGroup(3, 'group3', [], []),
        new UserGroup(4, 'group4', [], [])
      ];
    } else if (page === 2) {
      pageBody = [
        new UserGroup(5, 'group5', [], []),
        new UserGroup(6, 'group6', [], []),
        new UserGroup(7, 'group7', [], []),
        new UserGroup(8, 'group8', [], [])
      ];
    }
    return of(pageBody);
  }

  public revokePermissionToDataset(groupId: number, datasetId: string): Observable<null> {
    if (datasetId === datasetInDB.id) {
      datasetInDB.groups.splice(groupId, 1);
    }
    return of(null);
  }

  public grantPermissionToDataset(groupName: string, datasetId: string): Observable<null> {
    if (datasetId === datasetInDB.id) {
      datasetInDB.groups.push(groupName);
    }
    return of(null);
  }
}

class DatasetsServiceMock {
  public getManagementDataset(datasetId: string): Observable<DatasetPermissions> {
    if (datasetId === datasetInDB.id) {
      return of(datasetInDB);
    }
    return of(null);
  }
}

describe('DatasetsTableComponent', () => {
  let component: DatasetsTableComponent;
  let fixture: ComponentFixture<DatasetsTableComponent>;
  const usersGroupsServiceMock = new UsersGroupsServiceMock();
  const datasetsServiceMock = new DatasetsServiceMock();

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [
        DatasetsTableComponent,
      ],
      providers: [
        DatasetsService,
        { provide: UsersGroupsService, useValue: usersGroupsServiceMock },
        { provide: DatasetsService, useValue: datasetsServiceMock },
        provideHttpClientTesting()
      ],
      imports: [
        RouterTestingModule,
        StoreModule.forRoot({})
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(DatasetsTableComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should check if group is default for user', () => {
    const dataset = lodash.cloneDeep(datasetMock);
    expect(component.isDefaultGroup(dataset, 'any_dataset')).toBe(true);
    expect(component.isDefaultGroup(dataset, 'datasetId')).toBe(true);
    expect(component.isDefaultGroup(dataset, '')).toBe(false);
    expect(component.isDefaultGroup(dataset, undefined)).toBe(false);
    expect(component.isDefaultGroup(dataset, 'fakeEmail')).toBe(false);
    expect(component.isDefaultGroup(dataset, 'fakename')).toBe(false);
  });

  it('should remove group from dataset', () => {
    const getGroupSpy = jest.spyOn(usersGroupsServiceMock, 'getGroup');
    const revokePermissionToDatasetSpy = jest.spyOn(usersGroupsServiceMock, 'revokePermissionToDataset');
    const getManagementDatasetSpy = jest.spyOn(datasetsServiceMock, 'getManagementDataset');
    const dataset = lodash.cloneDeep(datasetMock);

    component.removeGroup(dataset, 'group2');
    expect(getGroupSpy).toHaveBeenCalledWith('group2');
    expect(revokePermissionToDatasetSpy).toHaveBeenCalledWith(1, 'datasetId',);
    expect(getManagementDatasetSpy).toHaveBeenCalledWith('datasetId');
    expect(dataset.id).toBe(datasetMock.id);
    expect(dataset.name).toBe(datasetMock.name);
    expect(dataset.groups).toStrictEqual(['group1', 'group3']);
    expect(dataset.users).toStrictEqual(datasetMock.users);
  });

  it('should add group to dataset', () => {
    const grantPermissionToDatasetSpy = jest.spyOn(usersGroupsServiceMock, 'grantPermissionToDataset');
    const getManagementDatasetSpy = jest.spyOn(datasetsServiceMock, 'getManagementDataset');
    const dataset = lodash.cloneDeep(datasetMock);

    component.addGroup(dataset, new Item('4', 'group4'));
    expect(grantPermissionToDatasetSpy).toHaveBeenCalledWith('group4', 'datasetId',);
    expect(getManagementDatasetSpy).toHaveBeenCalledWith('datasetId');
    expect(dataset.id).toBe(datasetMock.id);
    expect(dataset.name).toBe(datasetMock.name);
    expect(dataset.groups).toStrictEqual(['group1', 'group3', 'group4']);
    expect(dataset.users).toStrictEqual(datasetMock.users);
  });

  it('should get group names function', async() => {
    const getGroupsSpy = jest.spyOn(usersGroupsServiceMock, 'getGroups');
    const dataset = lodash.cloneDeep(datasetMock);
    dataset.groups = ['group1', 'group3'];

    const getGroupsLambda = component.getGroupNamesFunction(dataset);

    let page = await lastValueFrom(getGroupsLambda(1, 'search1'));
    expect(getGroupsSpy).toHaveBeenCalledWith(1, 'search1');
    expect(page).toStrictEqual(
      [
        new Item('2', 'group2'),
        new Item('4', 'group4')
      ]
    );

    page = await lastValueFrom(getGroupsLambda(2, 'search2'));

    expect(getGroupsSpy).toHaveBeenCalledWith(2, 'search2');
    expect(page).toStrictEqual(
      [
        new Item('5', 'group5'),
        new Item('6', 'group6'),
        new Item('7', 'group7'),
        new Item('8', 'group8')
      ]
    );
  });
});
