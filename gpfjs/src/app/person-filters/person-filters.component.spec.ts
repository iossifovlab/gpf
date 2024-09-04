import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';
import { PersonFiltersComponent } from './person-filters.component';
import { personFiltersReducer } from './person-filters.state';
import { StoreModule } from '@ngrx/store';
import { datasetIdReducer } from 'app/datasets/datasets.state';

describe('PersonFiltersComponent', () => {
  let component: PersonFiltersComponent;
  let fixture: ComponentFixture<PersonFiltersComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [PersonFiltersComponent, ErrorsAlertComponent],
      imports: [StoreModule.forRoot({personFilters: personFiltersReducer, datasetId: datasetIdReducer})],
    }).compileComponents();

    fixture = TestBed.createComponent(PersonFiltersComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
