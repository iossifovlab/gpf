import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ErrorsAlertComponent } from './errors-alert.component';

describe('ErrorsAlertComponent', () => {
  let component: ErrorsAlertComponent;
  let fixture: ComponentFixture<ErrorsAlertComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ErrorsAlertComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(ErrorsAlertComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
