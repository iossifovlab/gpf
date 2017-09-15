import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { GroupsBulkRemoveComponent } from './groups-bulk-remove.component';

describe('GroupsBulkRemoveComponent', () => {
  let component: GroupsBulkRemoveComponent;
  let fixture: ComponentFixture<GroupsBulkRemoveComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ GroupsBulkRemoveComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(GroupsBulkRemoveComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
