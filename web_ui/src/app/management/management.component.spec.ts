import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { ManagementComponent } from './management.component';
import { UsersService } from '../users/users.service';


describe('ManagementComponent', () => {
  let component: ManagementComponent;
  const usersService = {
    cachedUserInfo: jest.fn()
  };
  const routerMock = {
    navigate: jest.fn()
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ManagementComponent],
      providers: [
        { provide: Router, useValue: routerMock },
        { provide: UsersService, useValue: usersService }
      ]
    });
    component = TestBed.createComponent(ManagementComponent).componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize', () => {
    const routerNavigateSpy = jest.spyOn(routerMock, 'navigate');
    const cachedUserInfoSpy = jest.spyOn(usersService, 'cachedUserInfo');

    cachedUserInfoSpy.mockReturnValue({isAdministrator: true});
    component.ngOnInit();
    expect(routerNavigateSpy).not.toHaveBeenCalled();

    cachedUserInfoSpy.mockReturnValue({isAdministrator: false});
    component.ngOnInit();
    expect(routerNavigateSpy).toHaveBeenCalledWith(['/']);

    routerNavigateSpy.mockReset();

    cachedUserInfoSpy.mockReturnValue(undefined);
    component.ngOnInit();
    expect(routerNavigateSpy).toHaveBeenCalledWith(['/']);
  });
});
