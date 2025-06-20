import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { regionsFiltersReducer, setRegionsFilters } from 'app/regions-filter/regions-filter.state';
import { Store, StoreModule } from '@ngrx/store';
import { provideHttpClient } from '@angular/common/http';
import { ConfigService } from 'app/config/config.service';
import { of } from 'rxjs';
import { RegionsFilterComponent } from './regions-filter.component';
import { resetErrors, setErrors } from 'app/common/errors.state';
import { NO_ERRORS_SCHEMA } from '@angular/core';

describe('RegionsFilterComponent', () => {
  let component: RegionsFilterComponent;
  let fixture: ComponentFixture<RegionsFilterComponent>;
  let store: Store;
  // const instanceServiceMock = new InstanceServiceMock();

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [RegionsFilterComponent],
      imports: [
        NgbModule,
        RouterTestingModule,
        StoreModule.forRoot({ regionsFilter: regionsFiltersReducer })
      ],
      providers: [
        ConfigService,
        provideHttpClient(),
        // { provide: InstanceService, useValue: instanceServiceMock},
      ],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();

    fixture = TestBed.createComponent(RegionsFilterComponent);
    component = fixture.componentInstance;


    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    store = TestBed.inject(Store);
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should get regions from state', () => {
    jest.spyOn(store, 'select').mockReturnValue(of(['chrX:153693262', 'chr6:89780211']));
    component.genome = 'hg38';
    component.ngOnInit();
    expect(component.regionsFilter.regionsFilter).toBe('chrX:153693262\nchr6:89780211');
    expect(component.regionsFilter.genome).toBe('hg38');
  });

  it('should set regions', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    component.setRegionsFilter('chr5:148481536');
    expect(component.regionsFilter.regionsFilter).toBe('chr5:148481536');
    expect(dispatchSpy).toHaveBeenCalledWith(setRegionsFilters({regionsFilter: ['chr5:148481536']}));
  });

  it('should show error message when no regions are typed', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    component.setRegionsFilter('');
    expect(dispatchSpy).toHaveBeenCalledWith(setErrors({
      errors: {
        componentId: 'regionsFilter', errors: ['Add at least one region filter.']
      }
    }));
  });

  it('should show error message when invalid region is typed', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    component.setRegionsFilter('148481536');
    expect(dispatchSpy).toHaveBeenCalledWith(setErrors({
      errors: {
        componentId: 'regionsFilter', errors: ['Invalid region: 148481536']
      }
    }));

    component.setRegionsFilter('9:76710833-76710830:320-345');
    expect(dispatchSpy).toHaveBeenCalledWith(setErrors({
      errors: {
        componentId: 'regionsFilter', errors: ['Invalid region: 9:76710833-76710830:320-345']
      }
    }));

    component.setRegionsFilter('23');
    expect(dispatchSpy).toHaveBeenCalledWith(setErrors({
      errors: {
        componentId: 'regionsFilter', errors: ['Invalid region: 23']
      }
    }));
  });

  it('should validate region separated by commas', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    component.genome = 'hg38';
    component.setRegionsFilter('chr1:360,500,000-360,800,000');
    expect(dispatchSpy).not.toHaveBeenCalledWith();
  });


  it('should show error message if interval start is bigger', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    component.genome = 'hg38';
    component.setRegionsFilter('chr1:500-300');
    expect(dispatchSpy).toHaveBeenCalledWith(setErrors({
      errors: {
        componentId: 'regionsFilter', errors: ['Invalid region: chr1:500-300']
      }
    }));
  });

  it('should reset errors on component destruction', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    component.ngOnDestroy();
    expect(dispatchSpy).toHaveBeenCalledWith(resetErrors({componentId: 'regionsFilter'}));
  });
});
