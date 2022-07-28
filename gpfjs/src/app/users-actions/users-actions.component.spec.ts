import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NgxsModule } from '@ngxs/store';
import { User } from 'app/users/users';
import { UsersService } from 'app/users/users.service';
import { Observable, of } from 'rxjs';

import { UsersActionsComponent } from './users-actions.component';

/* rule not applicable for jest mocks */
/* eslint-disable @typescript-eslint/unbound-method */

class UsersServiceMock {
  public getUserInfo(): Observable<object> {
    return of({ email: 'mockMail@mail.com'});
  }

  public deleteUser(): object {
    return of({});
  }

  public resetUserPassword(): object {
    return of({});
  }
}

describe('UsersActionsComponent', () => {
  let component: UsersActionsComponent;
  let fixture: ComponentFixture<UsersActionsComponent>;

  const usersServiceMock = new UsersServiceMock();

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [
        UsersActionsComponent,
      ],
      providers: [
        {provide: UsersService, useValue: usersServiceMock},
        {provide: User, useValue: new User(0, '', '', [''], true, [''])}
      ],
      imports: [HttpClientTestingModule, RouterTestingModule, NgxsModule.forRoot([], {developmentMode: true})],
    }).compileComponents();

    fixture = TestBed.createComponent(UsersActionsComponent);
    component = fixture.componentInstance;
    component.user = new User(0, '', 'notMockMail@mail.com', [''], true, ['']);
    fixture.detectChanges();

    Object.defineProperty(window, 'location', {
      writable: true,
      value: { reload: jest.fn() },
    });
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize', () => {
    expect(component.user.email).toBe('notMockMail@mail.com');
    expect(component.showDeleteButton).toBe(true);
    component.user.email = 'mockMail@mail.com';
    component.ngOnInit();
    expect(component.showDeleteButton).toBe(false);
  });

  it('should delete user', () => {
    const deleteUserSpy = jest.spyOn(usersServiceMock, 'deleteUser');

    const user = new User(1, 'fakeUser', 'mockMail@mail.com', [''], true, ['']);
    component.deleteUser(user);
    expect(deleteUserSpy).toHaveBeenCalledTimes(1);
    expect(deleteUserSpy).toHaveBeenCalledWith(user);
    expect(window.location.reload).toHaveBeenCalledWith();
  });

  it('should reset user password', () => {
    const resetUserSpy = jest.spyOn(usersServiceMock, 'resetUserPassword');

    const user = new User(1, 'fakeUser', 'mockMail@mail.com', [''], true, ['']);
    component.resetPassword(user);
    expect(resetUserSpy).toHaveBeenCalledTimes(1);
    expect(resetUserSpy).toHaveBeenCalledWith(user);
    expect(window.location.reload).toHaveBeenCalledWith();
  });

  it('should get reset password popover message', () => {
    const expectedText = `'s password will be reset. `
      + `An email with reset instructions will be sent and they won't be able to login until they set a new password.`;

    expect(component.resetPasswordPopoverMessage(
      new User(1, 'fakeUser', 'mockMail@mail.com', [''], true, ['']))
    ).toStrictEqual(`(mockMail@mail.com) fakeUser` + expectedText);
    expect(component.resetPasswordPopoverMessage(
      new User(1, undefined, 'mockMail@mail.com', [''], true, ['']))
    ).toStrictEqual(`mockMail@mail.com` + expectedText);
    expect(component.resetPasswordPopoverMessage(
      new User(1, '', 'mockMail@mail.com', [''], true, ['']))
    ).toStrictEqual(`mockMail@mail.com` + expectedText);
  });

  it('should get delete user popover message', () => {
    const expectedText = ` will be deleted. This action is irrevertible!`;

    expect(component.deleteUserPopoverMessage(
      new User(1, 'fakeUser', 'mockMail@mail.com', [''], true, ['']))
    ).toStrictEqual(`(mockMail@mail.com) fakeUser` + expectedText);
    expect(component.deleteUserPopoverMessage(
      new User(1, undefined, 'mockMail@mail.com', [''], true, ['']))
    ).toStrictEqual(`mockMail@mail.com` + expectedText);
    expect(component.deleteUserPopoverMessage(
      new User(1, '', 'mockMail@mail.com', [''], true, ['']))
    ).toStrictEqual(`mockMail@mail.com` + expectedText);
  });
});
