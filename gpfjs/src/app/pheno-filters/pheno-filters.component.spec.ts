import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { PhenoFiltersComponent } from './pheno-filters.component';

describe('PhenoFiltersComponent', () => {
  let component: PhenoFiltersComponent;
  let fixture: ComponentFixture<PhenoFiltersComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PhenoFiltersComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PhenoFiltersComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
