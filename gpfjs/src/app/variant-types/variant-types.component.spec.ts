import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { VariantTypesComponent } from './variant-types.component';
import { DatasetsService } from 'app/datasets/datasets.service';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ConfigService } from 'app/config/config.service';
import { UsersService } from 'app/users/users.service';
import { RouterTestingModule } from '@angular/router/testing';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';
import { of } from 'rxjs';
import { CheckboxListComponent } from 'app/checkbox-list/checkbox-list.component';
import { initialState, setVariantTypes, variantTypesReducer } from './variant-types.state';
import { Store, StoreModule } from '@ngrx/store';

describe('VariantTypesComponent', () => {
  let component: VariantTypesComponent;
  let fixture: ComponentFixture<VariantTypesComponent>;
  let store: Store;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [VariantTypesComponent, ErrorsAlertComponent, CheckboxListComponent],
      providers: [
        DatasetsService,
        ConfigService,
        UsersService,
      ],
      imports: [HttpClientTestingModule, RouterTestingModule, StoreModule.forRoot({variantTypes: variantTypesReducer})]
    })
      .compileComponents();

    fixture = TestBed.createComponent(VariantTypesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should handle selected values input and/or restore state', () => {
    let dispatchSpy;
    store = TestBed.inject(Store);

    jest.spyOn(store, 'select').mockReturnValue(of(['value1', 'value2']));
    jest.spyOn(store, 'dispatch').mockReturnValue();

    dispatchSpy = jest.spyOn(store, 'dispatch');

    component.ngOnInit();
    expect(component.selectedVariantTypes).toStrictEqual(new Set(['value1', 'value2']));
    expect(dispatchSpy).not.toHaveBeenCalled();

    component.variantTypes = new Set(['value3']);

    jest.spyOn(store, 'select').mockReturnValue(of(initialState));
    dispatchSpy = jest.spyOn(component['store'], 'dispatch');

    component.ngOnInit();
    expect(component.selectedVariantTypes).toStrictEqual(new Set(['value3']));
    expect(dispatchSpy).toHaveBeenCalledWith({
      type: '[Genotype] Set variant types',
      variantTypes: ['value3']
    });
  });

  it('should update variant types', () => {
    component.selectedVariantTypes = undefined;
    store = TestBed.inject(Store);
    jest.spyOn(store, 'dispatch').mockReturnValue();

    const dispatchSpy = jest.spyOn(component['store'], 'dispatch');
    const mockSet = new Set(['value1', 'value2', 'value3']);

    component.updateVariantTypes(mockSet);

    expect(component.selectedVariantTypes).toStrictEqual(mockSet);
    expect(dispatchSpy).toHaveBeenNthCalledWith(1, setVariantTypes({variantTypes: [...mockSet]}));
  });
});
