import { ComponentFixture, TestBed } from '@angular/core/testing';

import { GeneBrowserFiltersComponent } from './gene-browser-filters.component';

describe('GeneBrowserFiltersComponent', () => {
  let component: GeneBrowserFiltersComponent;
  let fixture: ComponentFixture<GeneBrowserFiltersComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ GeneBrowserFiltersComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(GeneBrowserFiltersComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
