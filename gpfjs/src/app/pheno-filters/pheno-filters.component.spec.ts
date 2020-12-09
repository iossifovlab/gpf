import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';

import { PhenoFiltersComponent } from './pheno-filters.component';

describe('PhenoFiltersComponent', () => {
  let component: PhenoFiltersComponent;
  let fixture: ComponentFixture<PhenoFiltersComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PhenoFiltersComponent, ErrorsAlertComponent ]
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
