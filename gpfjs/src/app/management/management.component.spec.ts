import { of } from 'rxjs';

import { ManagementComponent } from './management.component';

describe('ManagementComponent', () => {
  let component: ManagementComponent;
  const usersService = {
    getUserInfoObservable: jest.fn()
  }
  const routerMock = {
    navigate: jest.fn()
  };

  beforeEach(() => {
    component = new ManagementComponent(routerMock as any, usersService as any);
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize', () => {
    const routerNavigateSpy = jest.spyOn(routerMock, 'navigate');
    const getUserInfoSpy = jest.spyOn(usersService, 'getUserInfoObservable');

    getUserInfoSpy.mockReturnValue(of({isAdministrator: true}));
    component.ngOnInit();
    expect(routerNavigateSpy).not.toBeCalled();

    getUserInfoSpy.mockReturnValue(of({isAdministrator: false}));
    component.ngOnInit();
    expect(routerNavigateSpy).toBeCalledWith(['/']);

    routerNavigateSpy.mockReset();

    getUserInfoSpy.mockReturnValue(of(undefined));
    component.ngOnInit();
    expect(routerNavigateSpy).toBeCalledWith(['/']);
  });
});
