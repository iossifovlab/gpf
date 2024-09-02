import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { CheckboxListComponent } from 'app/checkbox-list/checkbox-list.component';
import { ErrorsAlertComponent } from '../errors-alert/errors-alert.component';
import { InheritancetypesComponent } from './inheritancetypes.component';
import { inheritanceTypesReducer, setInheritanceTypes } from './inheritancetypes.state';
import { Store, StoreModule } from '@ngrx/store';

describe('InheritancetypesComponent', () => {
  let component: InheritancetypesComponent;
  let fixture: ComponentFixture<InheritancetypesComponent>;
  let store: Store;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [
        ErrorsAlertComponent,
        InheritancetypesComponent,
        CheckboxListComponent
      ],
      imports: [StoreModule.forRoot({inheritanceTypes: inheritanceTypesReducer})],
    }).compileComponents();
    store = TestBed.inject(Store);
    store.dispatch(setInheritanceTypes({inheritanceTypes: ['value1', 'value2']}));
    fixture = TestBed.createComponent(InheritancetypesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should handle selected values input and/or restore state', () => {
    component.ngOnChanges();
    expect(component.selectedValues).toStrictEqual(new Set(['value1', 'value2']));
    component.updateInheritanceTypes(new Set(['value3']));
    component.ngOnChanges();
    expect(component.selectedValues).toStrictEqual(new Set(['value3']));
  });

  it('should update variant types', () => {
    component.selectedValues = undefined;
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    const mockSet = new Set(['value1', 'value2', 'value3']);

    component.updateInheritanceTypes(mockSet);

    expect(component.selectedValues).toStrictEqual(mockSet);
    expect(dispatchSpy).toHaveBeenNthCalledWith(1, setInheritanceTypes({inheritanceTypes: [...mockSet]}));
  });
});
