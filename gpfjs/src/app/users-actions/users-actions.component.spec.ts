import { HttpClientTestingModule } from '@angular/common/http/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NgxsModule } from '@ngxs/store';
import { ConfigService } from 'app/config/config.service';
import { User } from 'app/users/users';
import { UsersService } from 'app/users/users.service';

import { UsersActionsComponent } from './users-actions.component';

describe('UsersActionsComponent', () => {
  let component: UsersActionsComponent;
  let fixture: ComponentFixture<UsersActionsComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [UsersActionsComponent],
      providers: [
        UsersService,
        ConfigService,
        {provide: User, useValue: new User(0, '', '', [''], true, [''])}],
      imports: [HttpClientTestingModule, RouterTestingModule, NgxsModule.forRoot([], {developmentMode: true})],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(UsersActionsComponent);
    component = fixture.componentInstance;
    component.user = new User(0, '', '', [''], true, ['']);
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
