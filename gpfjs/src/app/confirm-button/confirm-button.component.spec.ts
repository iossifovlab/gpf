import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { ConfirmButtonComponent } from './confirm-button.component';

describe('ConfirmButtonComponent', () => {
  let component: ConfirmButtonComponent;
  let fixture: ComponentFixture<ConfirmButtonComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ConfirmButtonComponent],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();

  beforeEach(() => {
    fixture = TestBed.createComponent(ConfirmButtonComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
