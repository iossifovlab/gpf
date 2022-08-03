import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { SortingButtonsComponent } from './sorting-buttons.component';

describe('SortingButtonsComponent', () => {
  let component: SortingButtonsComponent;
  let fixture: ComponentFixture<SortingButtonsComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [SortingButtonsComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(SortingButtonsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should emit sort event', () => {
    const emitSpy = jest.spyOn(component.sortEvent, 'emit');

    component.id = 'id1';
    component.emitSortEvent('order1');
    expect(emitSpy).toHaveBeenCalledWith({ id: 'id1', order: 'order1'});

    component.id = 'id2';
    component.emitSortEvent('order2');
    expect(emitSpy).toHaveBeenCalledWith({ id: 'id2', order: 'order2'});
  });

  it('should emit sort', () => {
    const emitSpy = jest.spyOn(component.sortEvent, 'emit');
    component.hideState = 0;
    component.id = 'id1';

    component.emitSort();
    expect(component.hideState).toBe(1);
    expect(emitSpy).toHaveBeenCalledWith({id: 'id1', order: 'desc'});

    component.emitSort();
    expect(component.hideState).toBe(-1);
    expect(emitSpy).toHaveBeenCalledWith({id: 'id1', order: 'asc'});
  });

  it('should reset hide state', () => {
    component.hideState = 0;
    component.resetHideState();
    expect(component.hideState).toBe(0);

    component.hideState = -1;
    component.resetHideState();
    expect(component.hideState).toBe(0);

    component.hideState = 1;
    component.resetHideState();
    expect(component.hideState).toBe(0);
  });
});
