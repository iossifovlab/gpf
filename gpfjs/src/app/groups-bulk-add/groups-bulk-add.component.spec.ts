import { HttpClientTestingModule } from '@angular/common/http/testing';
import { Component } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NgxsModule } from '@ngxs/store';
import { ConfigService } from 'app/config/config.service';
import { UsersGroupsService } from 'app/users-groups/users-groups.service';
import { User } from 'app/users/users';
import { UsersService } from 'app/users/users.service';
import { Observable, of } from 'rxjs';

import { GroupsBulkAddComponent } from './groups-bulk-add.component';

@Component({
  selector: 'gpf-groups-bulk-add',
  templateUrl: './groups-bulk-add.component.html',
  styleUrls: ['./groups-bulk-add.component.css']
})
export class MockGroupsBulkAddComponent extends GroupsBulkAddComponent{
  getUsersOrBack() {
    return new Observable<User[]>();
  }
}

describe('GroupsBulkAddComponent', () => {
  let component: MockGroupsBulkAddComponent;
  let fixture: ComponentFixture<MockGroupsBulkAddComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [MockGroupsBulkAddComponent],
      providers: [ConfigService, UsersService, UsersGroupsService],
      imports: [RouterTestingModule, HttpClientTestingModule, NgxsModule.forRoot([])]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MockGroupsBulkAddComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
