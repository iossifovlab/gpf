import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';
import { PersonFiltersComponent } from './person-filters.component';
import { personFiltersReducer } from './person-filters.state';
import { Store, StoreModule } from '@ngrx/store';
import { datasetIdReducer } from 'app/datasets/datasets.state';
import { Dataset } from 'app/datasets/datasets';
import { of } from 'rxjs';

describe('PersonFiltersComponent', () => {
  let component: PersonFiltersComponent;
  let fixture: ComponentFixture<PersonFiltersComponent>;
  let store: Store;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [PersonFiltersComponent, ErrorsAlertComponent],
      imports: [
        StoreModule.forRoot({personFilters: personFiltersReducer, datasetId: datasetIdReducer})
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(PersonFiltersComponent);
    component = fixture.componentInstance;
    component.dataset = {
      id: 'mockDataset',
      genotypeBrowserConfig: {
        familyFilters: [],
        personFilters: [],
      }
    } as Dataset;
    store = TestBed.inject(Store);
    jest.spyOn(store, 'select').mockReturnValue(of({
      familyFilters: [],
      personFilters: [],
    }));


    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
