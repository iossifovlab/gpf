import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { FamilyCountersComponent } from './family-counters.component';

describe('FamilyCountersComponent', () => {
  let component: FamilyCountersComponent;
  let fixture: ComponentFixture<FamilyCountersComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ FamilyCountersComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(FamilyCountersComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
