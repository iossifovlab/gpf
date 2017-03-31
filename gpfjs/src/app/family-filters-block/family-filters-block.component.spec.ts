import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { FamilyFiltersBlockComponent } from './family-filters-block.component';

describe('FamilyFiltersBlockComponent', () => {
  let component: FamilyFiltersBlockComponent;
  let fixture: ComponentFixture<FamilyFiltersBlockComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ FamilyFiltersBlockComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(FamilyFiltersBlockComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
