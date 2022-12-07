import { APP_BASE_HREF } from '@angular/common';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NgxsModule } from '@ngxs/store';
import { ConfigService } from 'app/config/config.service';
import { UserGroup } from 'app/users-groups/users-groups';
import { UsersGroupsService } from 'app/users-groups/users-groups.service';
import { User } from 'app/users/users';
import { UsersService } from 'app/users/users.service';
import { Observable, of } from 'rxjs';

import { UsersTableComponent } from './users-table.component';

class UsersGroupsServiceMock {
  public getGroups(page: number, searchTerm: string): Observable<UserGroup[]> {
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
}

class UsersServiceMock {
  public getUserInfo(): Observable<User> {
    return of(new User(1, 'fakeName', 'fakeEmail', [], true, []));
  }

  public removeUserGroup(user: User, group: string): Observable<object> {
    return of(new User(
      user.id,
      user.name,
      user.email,
      user.groups.filter(g => g !== group),
      user.hasPassword,
      user.allowedDatasets.filter(d => {
        if (group === 'group1') {
          return d !== 'dataset2' && d !== 'dataset3';
        } else if (group === 'group3') {
          return d!=='dataset1' && d!=='dataset4';
        } else {
          return false;
        }
      })
    ));
  }

  public updateUser(user: User): Observable<object> {
    return of(new User(
      user.id,
      user.name,
      user.email,
      user.groups,
      user.hasPassword,
      user.allowedDatasets.concat(
        user.groups.includes('group4') ? ['dataset4', 'dataset6'] :
          user.groups.includes('group3') ? ['dataset3', 'dataset5'] :[]
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
    expect(component.isDefaultGroup(user, 'fakeemail')).toBe(true);
    expect(component.isDefaultGroup(user, '')).toBe(false);
    expect(component.isDefaultGroup(user, undefined)).toBe(false);
    expect(component.isDefaultGroup(user, 'fakeEmail')).toBe(false);
    expect(component.isDefaultGroup(user, 'fakename')).toBe(false);
  });

  it('should remove group from user', () => {
    const user = new User(
      17,
      'fakeName',
      'fakeEmail',
      ['group1', 'group2', 'group3', 'group4'],
      true,
      ['dataset1', 'dataset2', 'dataset3', 'dataset4', 'dataset5'],
    );

    component.removeGroup(user, 'group3');
    expect(user).toStrictEqual(new User(
      17,
      'fakeName',
      'fakeEmail',
      ['group1', 'group2', 'group4'],
      true,
      ['dataset2', 'dataset3', 'dataset5']
    ));

    component.removeGroup(user, 'group1');
    expect(user).toStrictEqual(new User(
      17,
      'fakeName',
      'fakeEmail',
      ['group2', 'group4'],
      true,
      ['dataset5']
    ));
  });

  it('should add group to user', () => {
    const user = new User(
      17,
      'fakeName',
      'fakeEmail',
      ['group1', 'group2'],
      true,
      ['dataset1', 'dataset2'],
    );

    component.addGroup(user, {id: user.name, item: 'group3'});
    expect(user).toStrictEqual(new User(
      17,
      'fakeName',
      'fakeEmail',
      ['group1', 'group2', 'group3'],
      true,
      ['dataset1', 'dataset2', 'dataset3', 'dataset5'],
    ));

    component.addGroup(user, {id: user.name, item: 'group4'});
    expect(user).toStrictEqual(new User(
      17,
      'fakeName',
      'fakeEmail',
      ['group1', 'group2', 'group3', 'group4'],
      true,
      ['dataset1', 'dataset2', 'dataset3', 'dataset5', 'dataset4', 'dataset6'],
    ));
  });

  it('should get group names function', () => {
    const user = new User(
      17,
      'fakeName',
      'fakeEmail',
      ['group1', 'group2', 'group3', 'group4'],
      true,
      ['dataset1', 'dataset2', 'dataset3', 'dataset4', 'dataset5'],
    );
  });
});
