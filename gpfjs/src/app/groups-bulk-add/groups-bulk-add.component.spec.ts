import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { GroupsBulkAddComponent } from './groups-bulk-add.component';

describe('GroupsBulkAddComponent', () => {
  let component: GroupsBulkAddComponent;
  let fixture: ComponentFixture<GroupsBulkAddComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ GroupsBulkAddComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(GroupsBulkAddComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
