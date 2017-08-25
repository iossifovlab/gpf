import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { GroupsTableComponent } from './groups-table.component';

describe('GroupsTableComponent', () => {
  let component: GroupsTableComponent;
  let fixture: ComponentFixture<GroupsTableComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ GroupsTableComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(GroupsTableComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
