/* eslint-disable no-unused-vars, @typescript-eslint/no-unused-vars */
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { VariantTypesComponent } from './variant-types.component';
import { DatasetsService } from 'app/datasets/datasets.service';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ConfigService } from 'app/config/config.service';
import { UsersService } from 'app/users/users.service';
import { RouterTestingModule } from '@angular/router/testing';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';
// eslint-disable-next-line no-restricted-imports
import { of } from 'rxjs';
import { NgxsModule, StateStream, Store } from '@ngxs/store';
import { CheckboxListComponent } from 'app/checkbox-list/checkbox-list.component';
import { SetVariantTypes, VarianttypesState } from './variant-types.state';

describe('VariantTypesComponent', () => {
  let component: VariantTypesComponent;
  let fixture: ComponentFixture<VariantTypesComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [VariantTypesComponent, ErrorsAlertComponent, CheckboxListComponent],
      providers: [
        DatasetsService,
        ConfigService,
        UsersService,
      ],
      imports: [HttpClientTestingModule, RouterTestingModule, NgxsModule.forRoot([], {developmentMode: true})]
    })
      .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(VariantTypesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should handle selected values input and/or restore state', () => {
    let dispatchSpy;

    component['store'] = {
      selectOnce(f: VarianttypesState) {
        return of({variantTypes: ['value1', 'value2']});
      },
      dispatch(set: SetVariantTypes) {}
    } as any;
    dispatchSpy = jest.spyOn(component['store'], 'dispatch');
    component.ngOnChanges();
    expect(component.selectedVariantTypes).toEqual(new Set(['value1', 'value2']));
    expect(dispatchSpy).not.toHaveBeenCalled();

    component.selectedVariantTypes = new Set(['value3']);
    component['store'] = {
      selectOnce(f: VarianttypesState) {
        return of({variantTypes: []});
      },
      dispatch(set: SetVariantTypes) {}
    } as any;
    dispatchSpy = jest.spyOn(component['store'], 'dispatch');
    component.ngOnChanges();
    expect(component.selectedVariantTypes).toEqual(new Set(['value3']));
    expect(dispatchSpy).toHaveBeenCalled();

  });

  it('should update variant types', () => {
    component.selectedVariantTypes = undefined;
    component['store'] = { dispatch(set: SetVariantTypes) {} } as any;
    const dispatchSpy = jest.spyOn(component['store'], 'dispatch');
    const mockSet = new Set(['value1', 'value2', 'value3']);

    component.updateVariantTypes(mockSet);

    expect(component.selectedVariantTypes).toEqual(mockSet);
    expect(dispatchSpy).toHaveBeenNthCalledWith(1, new SetVariantTypes(mockSet));
  });
});
