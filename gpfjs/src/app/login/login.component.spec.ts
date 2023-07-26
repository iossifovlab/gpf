import { ComponentFixture, TestBed } from '@angular/core/testing';

import { LoginComponent } from './login.component';
import { Router } from '@angular/router';

describe('LoginComponent', () => {
  let component: LoginComponent;
  let fixture: ComponentFixture<LoginComponent>;
  let router: Router;

  beforeEach(async() => {
    await TestBed.configureTestingModule({
      declarations: [LoginComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(LoginComponent);
    component = fixture.componentInstance;
    router = TestBed.inject(Router);
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should spy on no state redirect', () => {
    const spy = jest.spyOn(router, 'navigate').mockReturnValue(Promise.resolve(true));
    component.ngOnInit();
    fixture.detectChanges();
    expect(spy).toHaveBeenCalledWith(['datasets']);
  });

  it('should test route redirect on init', () => {
    const spy = jest.spyOn(router, 'navigate').mockReturnValue(Promise.resolve(true));
    Object.defineProperty(window, 'location', {
      value: {
        href: ''
      },
      writable: true
    });
    // eslint-disable-next-line @typescript-eslint/naming-convention
    const state = btoa(JSON.stringify({ came_from: '/other' }));
    window.location.href = `http://mockUrl.mock?state=${state}`;
    component.ngOnInit();
    expect(spy).toHaveBeenCalledWith(['/other']);
  });
});
