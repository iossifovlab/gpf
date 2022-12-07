import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AddButtonComponent } from './add-button.component';

describe('AddButtonComponent', () => {
  let component: AddButtonComponent;
  let fixture: ComponentFixture<AddButtonComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [AddButtonComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(AddButtonComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should give image path prefix', () => {
    expect(component.imgPathPrefix).toBe('assets/');
  });

  it('should emit on click', () => {
    jest.spyOn(component.addFilter, 'emit').mockImplementation(() => null);
    component.add();
    expect(component.addFilter.emit).toHaveBeenCalledWith(null);
  });
});
