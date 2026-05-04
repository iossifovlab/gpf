import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';
import { FamilyIdsComponent } from './family-ids.component';
import { familyIdsReducer } from './family-ids.state';
import { Store, StoreModule } from '@ngrx/store';
import { of } from 'rxjs';

describe('FamilyIdsComponent', () => {
  let component: FamilyIdsComponent;
  let fixture: ComponentFixture<FamilyIdsComponent>;
  let store: Store;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [FamilyIdsComponent, ErrorsAlertComponent],
      imports: [FormsModule, StoreModule.forRoot({familyIds: familyIdsReducer})]
    }).compileComponents();

    fixture = TestBed.createComponent(FamilyIdsComponent);
    component = fixture.componentInstance;

    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    store = TestBed.inject(Store);
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should select family ids from state', () => {
    const selectSpy = jest.spyOn(store, 'select').mockReturnValue(of(['id1', 'id2', 'id3']));
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    const setFamilyIdsSpy = jest.spyOn(component, 'setFamilyIds');

    component.ngOnInit();

    expect(selectSpy).not.toHaveBeenCalledWith();
    expect(setFamilyIdsSpy).not.toHaveBeenCalledWith();
    expect(component.familyIds).toBe('id1\nid2\nid3');
    expect(dispatchSpy).not.toHaveBeenCalledWith();
  });
});
