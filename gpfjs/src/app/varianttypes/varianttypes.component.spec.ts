/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { VarianttypesComponent } from './varianttypes.component';
import { DatasetsService } from 'app/datasets/datasets.service';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ConfigService } from 'app/config/config.service';
import { UsersService } from 'app/users/users.service';
import { RouterTestingModule } from '@angular/router/testing';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';
// tslint:disable-next-line:import-blacklist
import { of } from 'rxjs';
import { NgxsModule, StateStream, Store } from '@ngxs/store';
import { CheckboxListComponent } from 'app/checkbox-list/checkbox-list.component';
import { SetVariantTypes } from './varianttypes.state';

describe('VarianttypesComponent', () => {
  let component: VarianttypesComponent;
  let fixture: ComponentFixture<VarianttypesComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [VarianttypesComponent, ErrorsAlertComponent, CheckboxListComponent],
      providers: [
        DatasetsService,
        ConfigService,
        UsersService,
      ],
      imports: [HttpClientTestingModule, RouterTestingModule, NgxsModule.forRoot([])]
    })
      .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(VarianttypesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should handle selected values input and/or restore state', () => {
    let dispatchSpy;

    component['store'] = {
      selectOnce(f) {
        return of({variantTypes: ['value1', 'value2']});
      },
      dispatch(set) {}
    } as any;
    dispatchSpy = spyOn(component['store'], 'dispatch');
    component.ngOnChanges();
    expect(component.selectedVariantTypes).toEqual(new Set(['value1', 'value2']));
    expect(dispatchSpy).not.toHaveBeenCalled();

    component.selectedVariantTypes = new Set(['value3']);
    component['store'] = {
      selectOnce(f) {
        return of({variantTypes: []});
      },
      dispatch(set) {}
    } as any;
    dispatchSpy = spyOn(component['store'], 'dispatch');
    component.ngOnChanges();
    expect(component.selectedVariantTypes).toEqual(new Set(['value3']));
    expect(dispatchSpy).toHaveBeenCalled();

  });

  it('should update variant types', () => {
    component.selectedVariantTypes = undefined;
    component['store'] = { dispatch(set) {} } as any;
    const dispatchSpy = spyOn(component['store'], 'dispatch');
    const mockSet = new Set(['value1', 'value2', 'value3']);

    component.updateVariantTypes(mockSet);

    expect(component.selectedVariantTypes).toEqual(mockSet);
    expect(dispatchSpy).toHaveBeenCalledOnceWith(new SetVariantTypes(mockSet));
  });
});
