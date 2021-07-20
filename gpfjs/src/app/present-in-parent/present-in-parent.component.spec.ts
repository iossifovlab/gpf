import { NO_ERRORS_SCHEMA } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { NgxsModule } from '@ngxs/store';
// tslint:disable-next-line:import-blacklist
import { of } from 'rxjs';

import { PresentInParentComponent } from './present-in-parent.component';
import { SetPresentInParentValues } from './present-in-parent.state';

describe('PresentInParentComponent', () => {
  let component: PresentInParentComponent;
  let fixture: ComponentFixture<PresentInParentComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PresentInParentComponent ],
      imports: [NgxsModule.forRoot([])],
      schemas: [NO_ERRORS_SCHEMA]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PresentInParentComponent);
    component = fixture.componentInstance;
    component['store'] = {
      selectOnce(f) {
        return of({
          presentInParent: ['value1', 'value2'],
          rarityType: 'rarityType',
          rarityIntervalStart: 'fakeStartNumber',
          rarityIntervalEnd: 'fakeEndNumber',
        });
      },
      dispatch(set) {}
    } as any;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should restore state on init', () => {
    component.ngOnInit();
    expect(component.selectedValues).toEqual(new Set(['value1', 'value2']));
    expect(component.selectedRarityType).toEqual('rarityType');
    expect(component.rarityIntervalStart).toEqual('fakeStartNumber' as any);
    expect(component.rarityIntervalEnd).toEqual('fakeEndNumber' as any);
  });

  it('should update rarity interval start', () => {
    component.rarityIntervalStart = undefined;
    component.rarityIntervalEnd = undefined;
    const updateStateSpy = spyOn(component, 'updateState');

    component.updateRarityIntervalStart('fakeStartNumber' as any);
    expect(component.rarityIntervalStart).toEqual('fakeStartNumber' as any);
    expect(component.rarityIntervalEnd).toEqual(undefined);
    expect(updateStateSpy).toHaveBeenCalled();
  });

  it('should update rarity interval end', () => {
    component.rarityIntervalStart = undefined;
    component.rarityIntervalEnd = undefined;
    const updateStateSpy = spyOn(component, 'updateState');

    component.updateRarityIntervalEnd('fakeEndNumber' as any);
    expect(component.rarityIntervalEnd).toEqual('fakeEndNumber' as any);
    expect(component.rarityIntervalStart).toEqual(undefined);
    expect(updateStateSpy).toHaveBeenCalled();
  });

  it('should update rarity type', () => {
    component.selectedRarityType = undefined;
    component.rarityIntervalStart = undefined;
    component.rarityIntervalEnd = undefined;
    const updateStateSpy = spyOn(component, 'updateState');

    component.updateRarityType('fakeRarityType' as any);
    expect(component.selectedRarityType).toEqual('fakeRarityType');
    expect(component.rarityIntervalStart).toEqual(undefined);
    expect(component.rarityIntervalEnd).toEqual(undefined);
    expect(updateStateSpy).toHaveBeenCalledTimes(1);

    component.updateRarityType('rare' as any);
    expect(component.selectedRarityType).toEqual('rare');
    expect(component.rarityIntervalStart).toEqual(0);
    expect(component.rarityIntervalEnd).toEqual(undefined);
    expect(updateStateSpy).toHaveBeenCalledTimes(2);
  });

  it('should update state', () => {
    const dispatchSpy = spyOn(component['store'], 'dispatch');

    component.updateState();
    expect(dispatchSpy).toHaveBeenCalledWith(new SetPresentInParentValues(
      new Set(['value1', 'value2']),
      'rarityType',
      'fakeStartNumber' as any,
      'fakeEndNumber' as any,
    ));
  });
});
