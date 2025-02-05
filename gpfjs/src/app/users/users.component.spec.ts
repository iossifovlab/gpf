import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, fakeAsync, TestBed } from '@angular/core/testing';
import { StoreModule } from '@ngrx/store';
import { UsersComponent } from './users.component';
import { UsersService } from './users.service';
import { AuthService } from 'app/auth.service';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ConfigService } from 'app/config/config.service';
import { APP_BASE_HREF } from '@angular/common';
import { UserInfo } from './users';
import { Router } from '@angular/router';
import { Observable, of } from 'rxjs';

class UsersServiceMock {
  public cachedUserInfo(): UserInfo {
    return {
      email: 'user@email.com',
      isAdministrator: true,
      loggedIn: true
    };
  }

  public logout(): Observable<object> {
    return of({});
  }
}

class AuthServiceMock {
  public generatePKCE(): string {
    return 'pkceMock';
  }
}
describe('UsersComponent', () => {
  let component: UsersComponent;
  let fixture: ComponentFixture<UsersComponent>;
  const usersServiceMock = new UsersServiceMock();
  const authServiceMock = new AuthServiceMock();


  beforeEach(fakeAsync(() => {
    TestBed.configureTestingModule({
      declarations: [
        UsersComponent
      ],
      providers: [
        {provide: UsersService, useValue: usersServiceMock},
        ConfigService,
        { provide: AuthService, useValue: authServiceMock },
        { provide: APP_BASE_HREF, useValue: '' },
        {
          provide: Router,
          useValue: {
            url: 'currentUrl'
          }
        },
        provideHttpClient(),
        provideHttpClientTesting()
      ],
      imports: [
        StoreModule.forRoot({}),
      ],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    fixture = TestBed.createComponent(UsersComponent);
    component = fixture.componentInstance;

    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should login user', () => {
    const state = {
      came_from: 'currentUrl'
    };
    const url = component['config'].rootUrl + component['baseHref']
    + 'o/authorize/?response_type=code'
    + '&code_challenge_method=S256'
    + '&code_challenge=pkceMock'
    + '&scope=read'
    + `&client_id=${component['config'].oauthClientId}`
    + `&redirect_uri=${window.location.origin}${component['baseHref']}login`
    + `&state=${btoa(JSON.stringify(state))}`;

    Object.defineProperty(window, 'location', {
      value: {
        href: url,
        origin: 'http://localhost'
      }
    });

    window.location.href = url;

    component.login();

    expect(window.location.href).toStrictEqual(url);
  });

  it('should logout user', () => {
    const logoutSpy = jest.spyOn(usersServiceMock, 'logout');
    component.logout();
    expect(logoutSpy).toHaveBeenCalledWith();
  });
});