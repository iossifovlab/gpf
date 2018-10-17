import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SmallRemoveButtonComponent } from './small-remove-button.component';

describe('SmallRemoveButtonComponent', () => {
  let component: SmallRemoveButtonComponent;
  let fixture: ComponentFixture<SmallRemoveButtonComponent>;

  beforeEach(async(() => {
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
