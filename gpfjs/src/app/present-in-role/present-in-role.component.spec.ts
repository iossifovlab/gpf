import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { PresentInRoleComponent } from './present-in-role.component';

describe('PresentInRoleComponent', () => {
  let component: PresentInRoleComponent;
  let fixture: ComponentFixture<PresentInRoleComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PresentInRoleComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PresentInRoleComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
