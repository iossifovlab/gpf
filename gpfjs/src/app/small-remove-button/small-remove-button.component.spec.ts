import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { SmallRemoveButtonComponent } from './small-remove-button.component';

describe('SmallRemoveButtonComponent', () => {
  let component: SmallRemoveButtonComponent;
  let fixture: ComponentFixture<SmallRemoveButtonComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ SmallRemoveButtonComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SmallRemoveButtonComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
