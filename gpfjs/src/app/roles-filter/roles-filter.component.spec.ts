import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { RolesFilterComponent } from './roles-filter.component';

describe('RolesFilterComponent', () => {
  let component: RolesFilterComponent;
  let fixture: ComponentFixture<RolesFilterComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ RolesFilterComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(RolesFilterComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
