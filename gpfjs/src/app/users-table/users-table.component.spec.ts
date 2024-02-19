import { APP_BASE_HREF } from '@angular/common';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NgxsModule } from '@ngxs/store';
import { ConfigService } from 'app/config/config.service';
import { UserGroup } from 'app/users-groups/users-groups';
import { Item } from 'app/item-add-menu/item-add-menu';
import { UsersGroupsService } from 'app/users-groups/users-groups.service';
import { User } from 'app/users/users';
import { UsersService } from 'app/users/users.service';
import { Observable, lastValueFrom, of } from 'rxjs';

import { UsersTableComponent } from './users-table.component';

const datasetMock1 = {datasetId: 'dataset1', datasetName: 'dataset1'};
const datasetMock2 = {datasetId: 'dataset2', datasetName: 'dataset2'};
const datasetMock3 = {datasetId: 'dataset3', datasetName: 'dataset3'};
const datasetMock4 = {datasetId: 'dataset4', datasetName: 'dataset4'};
const datasetMock5 = {datasetId: 'dataset5', datasetName: 'dataset5'};
const datasetMock6 = {datasetId: 'dataset6', datasetName: 'dataset6'};

const userMockConstructorArgs: [
  number,
  string,
  string,
  string[],
  boolean,
  { datasetId: string; datasetName: string}[]
] = [
  17,
  'fakeName',
  'fakeEmail',
  ['group1', 'group2', 'group3', 'group4'],
  true,
  [datasetMock1, datasetMock2, datasetMock3, datasetMock4, datasetMock5, datasetMock6]
];

const userMock = new User(...userMockConstructorArgs);

class UsersGroupsServiceMock {
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

  public removeUser(): Observable<null> {
    return of(null);
  }

  public addUser(): Observable<null> {
    return of(null);
  }
}

class UsersServiceMock {
  public getUsers(): Observable<User[]> {
    return of([
      new User(
        userMock.id,
        userMock.name,
        userMock.email,
        ['groupAfterUpdate'],
        userMock.hasPassword,
        [{datasetId: 'datasetIdAfterUpdate', datasetName: 'datasetNameAfterUpdate'}]
      )]);
  }

  public updateUser(user: User): Observable<object> {
    return of(new User(
      user.id,
      user.name,
      user.email,
      user.groups,
      user.hasPassword,
      user.allowedDatasets.concat(
        user.groups.includes('group4') ? [
          datasetMock4,
          datasetMock6,
        ] :
          user.groups.includes('group3') ? [
            datasetMock3,
            datasetMock5,
          ] : []
      )
    ));
  }
}

describe('UsersTableComponent', () => {
  let component: UsersTableComponent;
  let fixture: ComponentFixture<UsersTableComponent>;
  const usersServiceMock = new UsersServiceMock();
  const usersGroupsServiceMock = new UsersGroupsServiceMock();

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [
        UsersTableComponent
      ],
      providers: [
        UsersService,
        ConfigService,
        { provide: APP_BASE_HREF, useValue: '' },
        { provide: UsersService, useValue: usersServiceMock },
        { provide: UsersGroupsService, useValue: usersGroupsServiceMock }
      ],
      imports: [
        HttpClientTestingModule,
        RouterTestingModule,
        NgxsModule.forRoot([], {developmentMode: true})
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(UsersTableComponent);
    component = fixture.componentInstance;
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should check if group is default for user', () => {
    const user = new User(1, 'fakeName', 'fakeEmail', [], true, []);
    expect(component.isDefaultGroup(user, 'any_user')).toBe(true);
    expect(component.isDefaultGroup(user, 'fakeemail')).toBe(false);
    expect(component.isDefaultGroup(user, '')).toBe(false);
    expect(component.isDefaultGroup(user, undefined)).toBe(false);
    expect(component.isDefaultGroup(user, 'fakeEmail')).toBe(false);
    expect(component.isDefaultGroup(user, 'fakename')).toBe(false);
  });

  it('should remove group from user', () => {
    const removeUserSpy = jest.spyOn(usersGroupsServiceMock, 'removeUser');
    const getUsersSpy = jest.spyOn(usersServiceMock, 'getUsers');
    const user = new User(...userMockConstructorArgs);

    component.removeGroup(user, 'groupToRemove');
    expect(removeUserSpy).toHaveBeenCalledWith(userMockConstructorArgs[2], 'groupToRemove');
    expect(getUsersSpy).toHaveBeenCalledWith(1, 'fakeEmail');
    expect(user).toStrictEqual(new User(
      userMockConstructorArgs[0],
      userMockConstructorArgs[1],
      userMockConstructorArgs[2],
      ['groupAfterUpdate'],
      userMockConstructorArgs[4],
      [{datasetId: 'datasetIdAfterUpdate', datasetName: 'datasetNameAfterUpdate'}]
    ));
  });

  it('should add group to user', () => {
    const removeUserSpy = jest.spyOn(usersGroupsServiceMock, 'addUser');
    const getUsersSpy = jest.spyOn(usersServiceMock, 'getUsers');
    const user = new User(...userMockConstructorArgs);

    component.addGroup(user, {id: 'groupToAddId', name: 'groupToAdd'});
    expect(removeUserSpy).toHaveBeenCalledWith(userMockConstructorArgs[2], 'groupToAdd');
    expect(getUsersSpy).toHaveBeenCalledWith(1, 'fakeEmail');
    expect(user).toStrictEqual(new User(
      userMockConstructorArgs[0],
      userMockConstructorArgs[1],
      userMockConstructorArgs[2],
      ['groupAfterUpdate'],
      userMockConstructorArgs[4],
      [{datasetId: 'datasetIdAfterUpdate', datasetName: 'datasetNameAfterUpdate'}]
    ));
  });

  it('should get group names function', async() => {
    const getGroupsSpy = jest.spyOn(usersGroupsServiceMock, 'getGroups');
    const user = new User(...userMockConstructorArgs);
    user.groups = ['group1', 'group3'];

    const getGroupsLambda = component.getGroupNamesFunction(user);

    let page = await lastValueFrom(getGroupsLambda(1, 'search1'));
    expect(getGroupsSpy).toHaveBeenCalledWith(1, 'search1');
    expect(page).toStrictEqual(
      [new Item('2', 'group2'), new Item('4', 'group4')]
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
