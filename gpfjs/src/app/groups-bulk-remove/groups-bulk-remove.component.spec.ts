import { HttpClientTestingModule } from '@angular/common/http/testing';
import { Component } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigService } from 'app/config/config.service';
import { UsersGroupsService } from 'app/users-groups/users-groups.service';
import { User } from 'app/users/users';
import { UsersService } from 'app/users/users.service';
import { Observable } from 'rxjs';

import { GroupsBulkRemoveComponent } from './groups-bulk-remove.component';

@Component({
  selector: 'gpf-groups-bulk-remove',
  templateUrl: './groups-bulk-remove.component.html',
  styleUrls: ['./groups-bulk-remove.component.css']
})
export class MockGroupsBulkRemoveComponent extends GroupsBulkRemoveComponent {
  getUsersOrBack() {
    return new Observable<User[]>();
  }
}

describe('GroupsBulkRemoveComponent', () => {
  let component: MockGroupsBulkRemoveComponent;
  let fixture: ComponentFixture<MockGroupsBulkRemoveComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ MockGroupsBulkRemoveComponent ],
      providers: [
        {provide: ActivatedRoute, useValue: new ActivatedRoute()},
        UsersService,
        ConfigService,
        UsersGroupsService,
      ],
      imports: [RouterTestingModule, HttpClientTestingModule]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MockGroupsBulkRemoveComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
