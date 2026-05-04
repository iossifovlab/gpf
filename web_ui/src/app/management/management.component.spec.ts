import { ManagementComponent } from './management.component';


describe('ManagementComponent', () => {
  let component: ManagementComponent;
  const usersService = {
    cachedUserInfo: jest.fn()
  };
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
