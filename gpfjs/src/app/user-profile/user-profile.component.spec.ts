import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NgbNavModule } from '@ng-bootstrap/ng-bootstrap';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { QueryService } from 'app/query/query.service';
import { ResizeService } from 'app/table/resize.service';
import { UsersService } from 'app/users/users.service';
import { APP_BASE_HREF } from '@angular/common';

import { UserProfileComponent } from './user-profile.component';
import { StoreModule } from '@ngrx/store';
import { UserInfo } from 'app/users/users';
class UsersServiceMock {
  public cachedUserInfo(): UserInfo {
    return {
      email: 'userEmail',
      isAdministrator: false,
      loggedIn: true
    };
  }
}
describe('UserProfileComponent', () => {
  let component: UserProfileComponent;
  let fixture: ComponentFixture<UserProfileComponent>;
  const usersServiceMock = new UsersServiceMock();

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [
        UserProfileComponent,
      ],
      providers: [
        QueryService, ConfigService, ResizeService, DatasetsService,
        { provide: APP_BASE_HREF, useValue: '' },
        { provide: UsersService, useValue: usersServiceMock },

      ],
      imports: [
        RouterTestingModule, HttpClientTestingModule, NgbNavModule, StoreModule.forRoot({})
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(UserProfileComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
