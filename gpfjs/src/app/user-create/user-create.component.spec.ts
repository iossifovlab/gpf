import { HttpClientTestingModule } from '@angular/common/http/testing';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigService } from 'app/config/config.service';
import { UsersGroupsService } from 'app/users-groups/users-groups.service';
import { UsersService } from 'app/users/users.service';
import { NgMultiSelectDropDownModule } from 'ng-multiselect-dropdown';

import { UserCreateComponent } from './user-create.component';

describe('UserCreateComponent', () => {
  let component: UserCreateComponent;
  let fixture: ComponentFixture<UserCreateComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      providers: [UsersService, ConfigService, UsersGroupsService],
      declarations: [ UserCreateComponent ],
      imports: [HttpClientTestingModule, RouterTestingModule, FormsModule, NgMultiSelectDropDownModule]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(UserCreateComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
