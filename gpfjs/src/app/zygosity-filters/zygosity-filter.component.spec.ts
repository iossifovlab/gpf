import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ZygosityFilterComponent } from './zygosity-filter.component';
import {
  resetZygosityFilter,
  setZygosityFilter,
  zygosityFilterReducer,
  ZygosityFilterState
} from './zygosity-filter.state';
import { Store, StoreModule } from '@ngrx/store';
import { of } from 'rxjs';
import { resetErrors, setErrors } from 'app/common/errors.state';

describe('ZygosityFiltersComponent', () => {
  let component: ZygosityFilterComponent;
  let fixture: ComponentFixture<ZygosityFilterComponent>;
  let store: Store;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ZygosityFilterComponent],
      imports: [
        StoreModule.forRoot({zygosityFilter: zygosityFilterReducer})
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ZygosityFilterComponent);
    component = fixture.componentInstance;

    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    store = TestBed.inject(Store);
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should select zygosity filter from state for the correct component', () => {
    const zygosityStateMock: ZygosityFilterState[] = [
      {componentId: 'presentInChild', filter: 'homozygous'},
      {componentId: 'presentInParent', filter: 'heterozygous'},
    ];
    jest.spyOn(store, 'select').mockReturnValue(of(zygosityStateMock));
    component.parentComponent = 'presentInParent';
    component.ngOnInit();
    expect(component.selectedZygosityTypes).toStrictEqual(new Set<string>(['heterozygous']));
  });

  it('should select default zygosity filters', () => {
    jest.spyOn(store, 'select').mockReturnValue(of([]));
    const filters = ['homozygous', 'heterozygous'];
    component.ngOnInit();
    expect(component.selectedZygosityTypes).toStrictEqual(new Set<string>(filters));
  });

  it('should check zygosity filter', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    const validateStateSpy = jest.spyOn(component, 'validateState');
    component.selectedZygosityTypes = new Set<string>();
    component.parentComponent = 'pedigreeSelector';

    component.checkZygosityType('homozygous', true);
    expect(component.selectedZygosityTypes).toStrictEqual(new Set<string>(['homozygous']));
    expect(dispatchSpy).toHaveBeenCalledWith(setZygosityFilter({zygosityFilter: {
      componentId: 'pedigreeSelector',
      filter: 'homozygous'
    }}));
    expect(validateStateSpy).toHaveBeenCalledWith();
  });
  it('should uncheck zygosity filter', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    const validateStateSpy = jest.spyOn(component, 'validateState');
    component.selectedZygosityTypes = new Set<string>(['homozygous', 'heterozygous']);
    component.parentComponent = 'pedigreeSelector';

    component.checkZygosityType('homozygous', false);
    expect(component.selectedZygosityTypes).toStrictEqual(new Set<string>(['heterozygous']));
    expect(dispatchSpy).toHaveBeenCalledWith(setZygosityFilter({zygosityFilter: {
      componentId: 'pedigreeSelector',
      filter: 'heterozygous'
    }}));
    expect(validateStateSpy).toHaveBeenCalledWith();
  });

  it('should reset state when all filters are selected', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    const validateStateSpy = jest.spyOn(component, 'validateState');
    component.selectedZygosityTypes = new Set<string>(['heterozygous']);
    component.parentComponent = 'pedigreeSelector';
    component.zygosityTypes = ['homozygous', 'heterozygous'];

    component.checkZygosityType('homozygous', true);
    expect(component.selectedZygosityTypes).toStrictEqual(new Set<string>(['homozygous', 'heterozygous']));
    expect(dispatchSpy).toHaveBeenCalledWith(resetZygosityFilter({
      componentId: 'pedigreeSelector'
    }));
    expect(validateStateSpy).toHaveBeenCalledWith();
  });

  it('should dispatch error message when no filters are selected', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    component.selectedZygosityTypes = new Set<string>();
    component.parentComponent = 'pedigreeSelector';

    component.validateState();
    expect(dispatchSpy).toHaveBeenCalledWith(setErrors({
      errors: {
        componentId: 'zygosityFilter: pedigreeSelector', errors: ['Select at least one zygosity.']
      }
    }));
  });

  it('should reset errors state when at least one filter is selected', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    component.selectedZygosityTypes = new Set<string>(['heterozygous']);
    component.parentComponent = 'pedigreeSelector';

    component.validateState();
    expect(dispatchSpy).toHaveBeenCalledWith(resetErrors({
      componentId: 'zygosityFilter: pedigreeSelector'
    }));
  });
});
