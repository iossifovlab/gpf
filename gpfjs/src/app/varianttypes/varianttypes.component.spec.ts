/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { VarianttypesComponent } from './varianttypes.component';
import { StateRestoreService } from 'app/store/state-restore.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ConfigService } from 'app/config/config.service';
import { UsersService } from 'app/users/users.service';
import { RouterTestingModule } from '@angular/router/testing';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';
// tslint:disable-next-line:import-blacklist
import { of } from 'rxjs';


describe('VarianttypesComponent', () => {
  let component: VarianttypesComponent;
  let fixture: ComponentFixture<VarianttypesComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [VarianttypesComponent, ErrorsAlertComponent],
      providers: [StateRestoreService, DatasetsService, ConfigService, UsersService],
      imports: [HttpClientTestingModule, RouterTestingModule]
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

  it('should initialize', () => {
    const getStateSpy = spyOn(component['stateRestoreService'], 'getState');

    getStateSpy.and.returnValue(of({}));
    component.selectedVariantTypes = undefined;
    component.ngOnInit();
    expect(component.selectedVariantTypes).toEqual(undefined);

    getStateSpy.and.returnValue(of({variantTypes: ['fakeVariantTypes']}));
    component.selectedVariantTypes = undefined;
    component.ngOnInit();
    expect(component.selectedVariantTypes).toEqual(new Set(['fakeVariantTypes']));
  });

  it('should select all', () => {
    component.selectedVariantTypes = undefined;
    const mockVariantTypes = new Set(['fakeVariantType1', 'fakeVariantType2']);
    component.variantTypes = mockVariantTypes;

    component.selectAll();
    expect(component.selectedVariantTypes).toEqual(mockVariantTypes);
  });

  it('should select none', () => {
    component.selectedVariantTypes = undefined;

    component.selectNone();
    expect(component.selectedVariantTypes).toEqual(new Set());
  });


  it('should check variant types value', () => {
    component.selectedVariantTypes = new Set();

    component.variantTypesCheckValue('abcd', false);
    expect(component.selectedVariantTypes).toEqual(new Set([]));

    component.variantTypesCheckValue('sub', false);
    expect(component.selectedVariantTypes).toEqual(new Set(['sub']));
    component.variantTypesCheckValue('ins', false);
    expect(component.selectedVariantTypes).toEqual(new Set(['sub', 'ins']));
    component.variantTypesCheckValue('del', false);
    expect(component.selectedVariantTypes).toEqual(new Set(['sub', 'ins', 'del']));
    component.variantTypesCheckValue('CNV', false);
    expect(component.selectedVariantTypes).toEqual(new Set(['sub', 'ins', 'del', 'CNV']));
    component.variantTypesCheckValue('complex', false);
    expect(component.selectedVariantTypes).toEqual(new Set(['sub', 'ins', 'del', 'CNV', 'complex']));
    component.variantTypesCheckValue('TR', false);
    expect(component.selectedVariantTypes).toEqual(new Set(['sub', 'ins', 'del', 'CNV', 'complex', 'TR']));

    component.variantTypesCheckValue('sub', true);
    expect(component.selectedVariantTypes).toEqual(new Set(['ins', 'del', 'CNV', 'complex', 'TR']));
    component.variantTypesCheckValue('ins', true);
    expect(component.selectedVariantTypes).toEqual(new Set(['del', 'CNV', 'complex', 'TR']));
    component.variantTypesCheckValue('del', true);
    expect(component.selectedVariantTypes).toEqual(new Set(['CNV', 'complex', 'TR']));
    component.variantTypesCheckValue('CNV', true);
    expect(component.selectedVariantTypes).toEqual(new Set(['complex', 'TR']));
    component.variantTypesCheckValue('complex', true);
    expect(component.selectedVariantTypes).toEqual(new Set(['TR']));
    component.variantTypesCheckValue('TR', true);
    expect(component.selectedVariantTypes).toEqual(new Set([]));
  });

  it('should get state', () => {
    component.selectedVariantTypes = new Set(['fakeVariantType1', 'fakeVariantType2']);
    component.getState().take(1).subscribe(state =>
      expect(state).toEqual({ variantTypes: [ 'fakeVariantType1', 'fakeVariantType2' ] })
    );
  });
});
