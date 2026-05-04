import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { GenderComponent } from './gender.component';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';
import { Store, StoreModule } from '@ngrx/store';
import { addGender, gendersReducer, removeGender } from './gender.state';
import { of } from 'rxjs';

describe('GenderComponent', () => {
  let component: GenderComponent;
  let fixture: ComponentFixture<GenderComponent>;
  let store: Store;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [GenderComponent, ErrorsAlertComponent],
      imports: [StoreModule.forRoot({genders: gendersReducer})]
    })
      .compileComponents();
    fixture = TestBed.createComponent(GenderComponent);
    component = fixture.componentInstance;

    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    store = TestBed.inject(Store);
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('all genders should be selected by default', () => {
    jest.spyOn(store, 'select').mockReturnValue(of(['male', 'female', 'unspecified']));
    component.ngOnInit();
    expect(component.selectedGenders).toStrictEqual(['male', 'female', 'unspecified']);
  });

  it('all genders should be selected after selectAll', () => {
    component.selectAll();
    expect(component.selectedGenders).toStrictEqual(['male', 'female', 'unspecified']);
  });

  it('all genders should be un-selected after selectNone', () => {
    component.selectNone();
    expect(component.selectedGenders).toStrictEqual([]);
  });

  it('should set checked male value and save it to state', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch');

    component.genderCheckValue('male', true);
    expect(dispatchSpy).toHaveBeenCalledWith(addGender({gender: 'male'}));
    expect(component.selectedGenders).toStrictEqual(['male']);
  });

  it('should uncheck male value and remove it from state', () => {
    jest.spyOn(store, 'select').mockReturnValue(of(['male', 'female', 'unspecified']));
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    component.ngOnInit();

    component.genderCheckValue('male', false);
    expect(dispatchSpy).toHaveBeenCalledWith(removeGender({gender: 'male'}));
    expect(component.selectedGenders).toStrictEqual(['female', 'unspecified']);
  });
});
