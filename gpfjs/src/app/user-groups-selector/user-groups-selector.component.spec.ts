import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { UserGroupsSelectorComponent } from './user-groups-selector.component';

describe('UserGroupsSelectorComponent', () => {
  let component: UserGroupsSelectorComponent;
  let fixture: ComponentFixture<UserGroupsSelectorComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ UserGroupsSelectorComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(UserGroupsSelectorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
