import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { NgbNavModule } from '@ng-bootstrap/ng-bootstrap';
import { UsersGroupsService } from 'app/users-groups/users-groups.service';
import { UsersTableComponent } from 'app/users-table/users-table.component';
import { UsersService } from 'app/users/users.service';

import { UserManagementComponent } from './user-management.component';
import { DatasetsService } from 'app/datasets/datasets.service';
import { User } from 'app/users/users';
import { Observable, of } from 'rxjs';
import { UserGroup } from 'app/users-groups/users-groups';
import { DatasetPermissions } from 'app/datasets-table/datasets-table';
import { FormsModule } from '@angular/forms';
import { RouterTestingModule } from '@angular/router/testing';
import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';


class UsersGroupsServiceMock {
  public getGroups(page: number, searchTerm: string): Observable<UserGroup[]> {
    let pageBody: UserGroup[];
    if (page === 1) {
      pageBody = [
        new UserGroup(1, 'group1', [], []),
        new UserGroup(2, 'group2', [], []),
      ];
    } else if (page === 2) {
      pageBody = [
        new UserGroup(3, 'group3', [], []),
        new UserGroup(4, 'group4', [], []),
      ];
    }
    return of(pageBody);
  }
}

class UsersServiceMock {
  public getUsers(page: number, searchTerm: string): Observable<User[]> {
    let pageBody: User[];
    if (page === 1) {
      pageBody = [
        new User(1, 'user1', 'user1email', ['any_user', 'a', 'b', 'c', 'user1email'], true, []),
        new User(2, 'user2', 'user2email', ['any_user', 'a', 'b', 'c', 'user2email'], true, []),
        new User(3, 'user3', 'user3email', ['any_user', 'a', 'b', 'c', 'user3email'], true, []),
      ];
    } else if (page === 2) {
      pageBody = [
        new User(4, 'user4', 'user4email', ['any_user', 'a', 'b', 'c', 'user4email'], true, []),
        new User(5, 'user5', 'user5email', ['any_user', 'a', 'b', 'c', 'user5email'], true, []),
        new User(6, 'user6', 'user6email', ['any_user', 'a', 'b', 'c', 'user6email'], true, []),
      ];
    }
    return of(pageBody);
  }

  public getUserInfo(): Observable<User> {
    return of(new User(
      1,
      'userMame',
      'userEmail',
      ['group'],
      true,
      [{datasetId: 'datasetId', datasetName: 'datasetName'}]
    ));
  }
}

class DatasetsServiceMock {
  public getManagementDatasets(page: number, searchTerm: string): Observable<DatasetPermissions[]> {
    let pageBody: DatasetPermissions[];
    if (page === 1) {
      pageBody = [
        new DatasetPermissions('1', 'dataset1', [], []),
        new DatasetPermissions('2', 'dataset2', [], []),
      ];
    } else if (page === 2) {
      pageBody = [
        new DatasetPermissions('3', 'dataset3', [], []),
        new DatasetPermissions('4', 'dataset4', [], []),
      ];
    }
    return of(pageBody);
  }
}

describe('UserManagementComponent', () => {
  let component: UserManagementComponent;
  let fixture: ComponentFixture<UserManagementComponent>;
  const usersServiceMock = new UsersServiceMock();
  const usersGroupsServiceMock = new UsersGroupsServiceMock();
  const datasetsServiceMock = new DatasetsServiceMock();

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [
        UserManagementComponent,
        UsersTableComponent,
      ],
      providers: [
        { provide: UsersService, useValue: usersServiceMock },
        { provide: UsersGroupsService, useValue: usersGroupsServiceMock },
        { provide: DatasetsService, useValue: datasetsServiceMock }
      ],
      imports: [
        HttpClientTestingModule,
        NgbNavModule,
        FormsModule,
        RouterTestingModule
      ],
      schemas: [
        CUSTOM_ELEMENTS_SCHEMA
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(UserManagementComponent);
    component = fixture.componentInstance;
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize', () => {
    const focusSearchBoxSpy = jest.spyOn(component, 'focusSearchBox');

    component.ngOnInit();
    expect(focusSearchBoxSpy).toHaveBeenCalledWith();
    expect(component.users).toStrictEqual([
      new User(1, 'user1', 'user1email', ['any_user', 'a', 'b', 'c', 'user1email',], true, []),
      new User(2, 'user2', 'user2email', ['any_user', 'a', 'b', 'c', 'user2email',], true, []),
      new User(3, 'user3', 'user3email', ['any_user', 'a', 'b', 'c', 'user3email',], true, []),
    ]);
    expect(component.groups).toStrictEqual([]);
    expect(component.datasets).toStrictEqual([]);
    expect(component.currentUserEmail).toBe('userEmail');
  });

  it('should search', () => {
    component.switchTableName('GROUPS');
    component.groups = [
      new UserGroup(10, 'group10', [], []),
      new UserGroup(11, 'group11', [], []),
    ];

    component.search('someValue');
    expect(component.searchText).toBe('someValue');
    expect(component.groups).toStrictEqual([
      new UserGroup(1, 'group1', [], []),
      new UserGroup(2, 'group2', [], []),
    ]);
  });

  it('should reset tables data', () => {
    component.switchTableName('GROUPS');
    component.users = [
      new User(1, 'user1', 'user1email', ['user1email'], true, [])
    ];
    component.groups = [
      new UserGroup(10, 'group10', [], [])
    ];
    component.datasets = [
      new DatasetPermissions('1', 'dataset1', [], [])
    ];

    component.resetTablesData();
    expect(component.users).toStrictEqual([]);
    expect(component.groups).toStrictEqual([]);
    expect(component.datasets).toStrictEqual([]);
  });

  it('should update table on scroll', () => {
    fixture.detectChanges();

    expect(component.users).toStrictEqual([
      new User(1, 'user1', 'user1email', ['any_user', 'a', 'b', 'c', 'user1email'], true, []),
      new User(2, 'user2', 'user2email', ['any_user', 'a', 'b', 'c', 'user2email'], true, []),
      new User(3, 'user3', 'user3email', ['any_user', 'a', 'b', 'c', 'user3email'], true, [])
    ]);

    window.scrollY = 100;
    window.innerHeight = 200;
    Object.defineProperty(document.body, 'scrollHeight', {value: 2000});

    window.dispatchEvent(new CustomEvent('scroll'));

    expect(component.users).toStrictEqual([
      new User(1, 'user1', 'user1email', ['any_user', 'a', 'b', 'c', 'user1email'], true, []),
      new User(2, 'user2', 'user2email', ['any_user', 'a', 'b', 'c', 'user2email'], true, []),
      new User(3, 'user3', 'user3email', ['any_user', 'a', 'b', 'c', 'user3email'], true, [])
    ]);

    window.scrollY = 100;
    window.innerHeight = 1800;
    Object.defineProperty(document.body, 'scrollHeight', {value: 2000});

    window.dispatchEvent(new CustomEvent('scroll'));

    expect(component.users).toStrictEqual([
      new User(1, 'user1', 'user1email', ['any_user', 'a', 'b', 'c', 'user1email'], true, []),
      new User(2, 'user2', 'user2email', ['any_user', 'a', 'b', 'c', 'user2email'], true, []),
      new User(3, 'user3', 'user3email', ['any_user', 'a', 'b', 'c', 'user3email'], true, []),
      new User(4, 'user4', 'user4email', ['any_user', 'a', 'b', 'c', 'user4email'], true, []),
      new User(5, 'user5', 'user5email', ['any_user', 'a', 'b', 'c', 'user5email'], true, []),
      new User(6, 'user6', 'user6email', ['any_user', 'a', 'b', 'c', 'user6email'], true, [])
    ]);
  });

  it('should switch table name', () => {
    component.searchText = 'something';
    component.users = [
      new User(1, 'user1', 'user1email', ['user1email'], true, [])
    ];

    component.switchTableName('DATASETS');
    expect(component.searchText).toBe('');
    expect(component.users).toStrictEqual([]);
    expect(component.groups).toStrictEqual([]);
    expect(component.datasets).toStrictEqual([
      new DatasetPermissions('1', 'dataset1', [], []),
      new DatasetPermissions('2', 'dataset2', [], [])
    ]);
  });

  it('should update users table data', () => {
    component.updateCurrentTable();
    expect(component.users).toStrictEqual([
      new User(1, 'user1', 'user1email', ['any_user', 'a', 'b', 'c', 'user1email',], true, []),
      new User(2, 'user2', 'user2email', ['any_user', 'a', 'b', 'c', 'user2email',], true, []),
      new User(3, 'user3', 'user3email', ['any_user', 'a', 'b', 'c', 'user3email'], true, [])
    ]);

    component.updateCurrentTable();
    expect(component.users).toStrictEqual([
      new User(1, 'user1', 'user1email', ['any_user', 'a', 'b', 'c', 'user1email',], true, []),
      new User(2, 'user2', 'user2email', ['any_user', 'a', 'b', 'c', 'user2email',], true, []),
      new User(3, 'user3', 'user3email', ['any_user', 'a', 'b', 'c', 'user3email',], true, []),
      new User(4, 'user4', 'user4email', ['any_user', 'a', 'b', 'c', 'user4email',], true, []),
      new User(5, 'user5', 'user5email', ['any_user', 'a', 'b', 'c', 'user5email',], true, []),
      new User(6, 'user6', 'user6email', ['any_user', 'a', 'b', 'c', 'user6email',], true, [])
    ]);
  });

  it('should update groups table data', () => {
    component.switchTableName('GROUPS');

    expect(component.groups).toStrictEqual([
      new UserGroup(1, 'group1', [], []),
      new UserGroup(2, 'group2', [], [])
    ]);

    component.updateCurrentTable();
    expect(component.groups).toStrictEqual([
      new UserGroup(1, 'group1', [], []),
      new UserGroup(2, 'group2', [], []),
      new UserGroup(3, 'group3', [], []),
      new UserGroup(4, 'group4', [], [])
    ]);
  });

  it('should update datasets table data', () => {
    component.switchTableName('DATASETS');

    expect(component.datasets).toStrictEqual([
      new DatasetPermissions('1', 'dataset1', [], []),
      new DatasetPermissions('2', 'dataset2', [], [])
    ]);

    component.updateCurrentTable();
    expect(component.datasets).toStrictEqual([
      new DatasetPermissions('1', 'dataset1', [], []),
      new DatasetPermissions('2', 'dataset2', [], []),
      new DatasetPermissions('3', 'dataset3', [], []),
      new DatasetPermissions('4', 'dataset4', [], [])
    ]);
  });
});
