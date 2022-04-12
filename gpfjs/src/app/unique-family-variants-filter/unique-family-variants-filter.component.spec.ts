import { ComponentFixture, TestBed } from '@angular/core/testing';

import { UniqueFamilyVariantsFilterComponent } from './unique-family-variants-filter.component';

describe('UniqueFamilyVariantsFilterComponent', () => {
  let component: UniqueFamilyVariantsFilterComponent;
  let fixture: ComponentFixture<UniqueFamilyVariantsFilterComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ UniqueFamilyVariantsFilterComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(UniqueFamilyVariantsFilterComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
