import { HttpClientTestingModule } from '@angular/common/http/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfirmationPopoverDirective, ConfirmationPopoverModule } from 'angular-confirmation-popover';
import { ConfirmationPopoverOptions } from 'angular-confirmation-popover/lib/confirmation-popover-options.provider';
import { ConfirmationPopoverWindowComponent } from 'angular-confirmation-popover/lib/confirmation-popover-window.component';
import { ConfigService } from 'app/config/config.service';
import { User } from 'app/users/users';
import { UsersService } from 'app/users/users.service';

import { UsersActionsComponent } from './users-actions.component';

describe('UsersActionsComponent', () => {
  let component: UsersActionsComponent;
  let fixture: ComponentFixture<UsersActionsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ UsersActionsComponent ],
      providers: [
        UsersService,
        ConfigService,
        {provide: User, useValue: new User(0, '', '', [''], true, [''])}],
      imports: [HttpClientTestingModule, RouterTestingModule],
      schemas: [NO_ERRORS_SCHEMA]
    })
    .compileComponents();
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
