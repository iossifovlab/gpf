import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { NgMultiSelectDropDownModule } from 'ng-multiselect-dropdown';

import { UserGroupsSelectorComponent } from './user-groups-selector.component';

describe('UserGroupsSelectorComponent', () => {
  let component: UserGroupsSelectorComponent;
  let fixture: ComponentFixture<UserGroupsSelectorComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [UserGroupsSelectorComponent],
      imports: [FormsModule, NgMultiSelectDropDownModule]
    }).compileComponents();
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
