import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { VariantTypesComponent } from './variant-types.component';
import { DatasetsService } from 'app/datasets/datasets.service';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ConfigService } from 'app/config/config.service';
import { UsersService } from 'app/users/users.service';
import { RouterTestingModule } from '@angular/router/testing';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';
import { of } from 'rxjs';
import { CheckboxListComponent } from 'app/checkbox-list/checkbox-list.component';
import { setVariantTypes, variantTypesReducer } from './variant-types.state';
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
        provideHttpClientTesting()
      ],
      imports: [RouterTestingModule, StoreModule.forRoot({variantTypes: variantTypesReducer})]
    })
      .compileComponents();

    fixture = TestBed.createComponent(VariantTypesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should restore state', () => {
    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    store = TestBed.inject(Store);
    const dispatchSpy = jest.spyOn(store, 'dispatch');

    jest.spyOn(store, 'select').mockReturnValue(of(['value1', 'value2']));

    component.ngOnInit();
    expect(component.selectedVariantTypes).toStrictEqual(new Set(['value1', 'value2']));
    expect(dispatchSpy).not.toHaveBeenCalledWith(setVariantTypes({ variantTypes: ['value1', 'value2'] }));
  });

  it('should update variant types', () => {
    component.selectedVariantTypes = undefined;
    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    store = TestBed.inject(Store);
    jest.spyOn(store, 'dispatch').mockReturnValue();

    const dispatchSpy = jest.spyOn(component['store'], 'dispatch');
    const mockSet = new Set(['value1', 'value2', 'value3']);

    component.updateVariantTypes(mockSet);

    expect(component.selectedVariantTypes).toStrictEqual(mockSet);
    expect(dispatchSpy).toHaveBeenNthCalledWith(2, setVariantTypes({variantTypes: [...mockSet]}));
  });
});
