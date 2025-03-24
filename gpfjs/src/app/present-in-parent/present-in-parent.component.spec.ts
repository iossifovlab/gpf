import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { of } from 'rxjs';
import { PresentInParentComponent } from './present-in-parent.component';
import { presentInParentReducer, setPresentInParent } from './present-in-parent.state';
import { Store, StoreModule } from '@ngrx/store';

describe('PresentInParentComponent', () => {
  let component: PresentInParentComponent;
  let fixture: ComponentFixture<PresentInParentComponent>;
  let store: Store;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [PresentInParentComponent],
      imports: [StoreModule.forRoot({presentInParent: presentInParentReducer})],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();
    fixture = TestBed.createComponent(PresentInParentComponent);
    component = fixture.componentInstance;

    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    store = TestBed.inject(Store);

    jest.spyOn(store, 'select').mockReturnValue(of({
      presentInParent: ['value1', 'value2'],
      rarity: {
        rarityType: 'rarityType',
        rarityIntervalStart: -12,
        rarityIntervalEnd: -11,
      }
    }));

    jest.spyOn(store, 'dispatch').mockReturnValue();
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should restore state on init', () => {
    component.ngOnInit();
    expect(component.selectedValues).toStrictEqual(new Set(['value1', 'value2']));
    expect(component.selectedRarityType).toBe('rarityType');
    expect(component.rarityIntervalStart).toBe(-12);
    expect(component.rarityIntervalEnd).toBe(-11);
  });

  it('should update rarity interval start', () => {
    component.rarityIntervalStart = undefined;
    component.rarityIntervalEnd = undefined;
    const updateStateSpy = jest.spyOn(component, 'updateState');

    component.updateRarityIntervalStart(6);
    expect(component.rarityIntervalStart).toBe(6);
    expect(component.rarityIntervalEnd).toBeUndefined();
    expect(updateStateSpy).toHaveBeenCalledWith();
  });

  it('should update rarity interval end', () => {
    component.rarityIntervalStart = undefined;
    component.rarityIntervalEnd = undefined;
    const updateStateSpy = jest.spyOn(component, 'updateState');

    component.updateRarityIntervalEnd(100);
    expect(component.rarityIntervalEnd).toBe(100);
    expect(component.rarityIntervalStart).toBeUndefined();
    expect(updateStateSpy).toHaveBeenCalledWith();
  });

  it('should update rarity type', () => {
    component.rarityIntervalStart = 0;
    component.rarityIntervalEnd = 2;
    const updateStateSpy = jest.spyOn(component, 'updateState');

    component.updateRarityType('rare');
    expect(component.selectedRarityType).toBe('rare');
    expect(component.rarityIntervalStart).toBe(0);
    expect(component.rarityIntervalEnd).toBe(1);
    expect(updateStateSpy).toHaveBeenCalledTimes(1);

    component.updateRarityIntervalStart(1.23);
    expect(updateStateSpy).toHaveBeenCalledTimes(2);

    component.updateRarityType('ultraRare');
    expect(component.selectedRarityType).toBe('ultraRare');
    expect(component.rarityIntervalStart).toBe(0);
    expect(component.rarityIntervalEnd).toBe(1);
    expect(updateStateSpy).toHaveBeenCalledTimes(3);
  });

  it('should set default rarity type and intervals when no values were selected', () => {
    component.rarityIntervalStart = undefined;
    component.rarityIntervalEnd = undefined;
    component.selectedValues = null;
    component.selectedRarityType = '';
    const updateStateSpy = jest.spyOn(component, 'updateState');

    component.updatePresentInParent(new Set<string>([]));
    expect(component.rarityIntervalStart).toBe(0);
    expect(component.rarityIntervalEnd).toBe(1);
    expect(component.selectedRarityType).toBe('ultraRare');
    expect(updateStateSpy).toHaveBeenCalledWith();
  });

  it('should not set rarity type when selecting "neither"', () => {
    component.rarityIntervalStart = undefined;
    component.rarityIntervalEnd = undefined;
    component.selectedValues = null;
    component.selectedRarityType = '';
    const updateStateSpy = jest.spyOn(component, 'updateState');

    component.updatePresentInParent(new Set(['neither']));
    expect(component.rarityIntervalStart).toBeUndefined();
    expect(component.rarityIntervalEnd).toBeUndefined();
    expect(component.selectedRarityType).toBe('');
    expect(updateStateSpy).toHaveBeenCalledWith();
  });

  it('should set default rarity type when selecting more than one values', () => {
    component.rarityIntervalStart = undefined;
    component.rarityIntervalEnd = undefined;
    component.selectedValues = null;
    component.selectedRarityType = '';
    const updateStateSpy = jest.spyOn(component, 'updateState');

    component.updatePresentInParent(new Set(['father only', 'neither']));
    expect(component.rarityIntervalStart).toBeUndefined();
    expect(component.rarityIntervalEnd).toBeUndefined();
    expect(component.selectedRarityType).toBe('ultraRare');
    expect(updateStateSpy).toHaveBeenCalledWith();
  });

  it('should update state', () => {
    const dispatchSpy = jest.spyOn(component['store'], 'dispatch');

    component.updateState();
    expect(dispatchSpy).toHaveBeenCalledWith(setPresentInParent({
      presentInParent: {
        presentInParent: ['value1', 'value2'],
        rarity: {
          rarityType: 'rarityType',
          rarityIntervalStart: -12,
          rarityIntervalEnd: -11
        }
      }
    }));
  });

  it('should set default present in parent values when study has denovo', () => {
    jest.spyOn(store, 'select').mockReturnValueOnce(of({presentInParent: [], rarity: null}));
    component.hasDenovo = true;
    component.presentInParentValues = new Set([
      'mother only', 'father only', 'mother and father', 'neither'
    ]);

    component.ngOnInit();
    expect(component.selectedValues).toStrictEqual(new Set(['neither']));
  });

  it('should set default present in parent values when study doesn\'t have denovo', () => {
    jest.spyOn(store, 'select').mockReturnValueOnce(of({presentInParent: [], rarity: null}));
    component.hasDenovo = false;
    const allValues = new Set([
      'mother only', 'father only', 'mother and father', 'neither'
    ]);
    component.presentInParentValues = allValues;

    component.ngOnInit();
    expect(component.selectedValues).toStrictEqual(allValues);
  });
});
