import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { FamilyTypeFilterComponent } from './family-type-filter.component';

describe('FamilyTypeFilterComponent', () => {
  let component: FamilyTypeFilterComponent;
  let fixture: ComponentFixture<FamilyTypeFilterComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ FamilyTypeFilterComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(FamilyTypeFilterComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
