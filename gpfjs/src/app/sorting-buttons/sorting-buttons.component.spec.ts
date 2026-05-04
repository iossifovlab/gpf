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

  it('should emit sort', () => {
    const emitSpy = jest.spyOn(component.sortEvent, 'emit');
    component.sortState = 0;
    component.id = 'id1';

    component.emitSort();
    expect(component.sortState).toBe(1);
    expect(emitSpy).toHaveBeenCalledWith({id: 'id1', order: 'desc'});

    component.emitSort();
    expect(component.sortState).toBe(-1);
    expect(emitSpy).toHaveBeenCalledWith({id: 'id1', order: 'asc'});
  });

  it('should reset hide state', () => {
    component.sortState = 0;
    component.resetSortState();
    expect(component.sortState).toBe(0);

    component.sortState = -1;
    component.resetSortState();
    expect(component.sortState).toBe(0);

    component.sortState = 1;
    component.resetSortState();
    expect(component.sortState).toBe(0);
  });
});
