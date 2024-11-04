import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { GenderComponent } from './gender.component';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';
import { Store, StoreModule } from '@ngrx/store';
import { addGender, gendersReducer, removeGender } from './gender.state';
import { Gender } from './gender';


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
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('both genders should be selected after create', () => {
    expect(component.gender.male).toBeTruthy();
    expect(component.gender.female).toBeTruthy();
  });

  it('both genders should be selected after selectAll', () => {
    component.selectAll();

    expect(component.gender.male).toBeTruthy();
    expect(component.gender.female).toBeTruthy();
  });

  it('both genders should be un-selected after selectNone', () => {
    component.selectNone();

    expect(component.gender.male).toBe(false);
    expect(component.gender.female).toBe(false);
  });

  it('should set checked male value and save it to state', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch');

    component.gender = new Gender();

    component.genderCheckValue('male', true);
    expect(dispatchSpy).toHaveBeenCalledWith(addGender({gender: 'male'}));
  });

  it('should unchecke male value and remove it to state', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch');

    component.gender = new Gender();
    component.gender.male = true;

    component.genderCheckValue('male', false);
    expect(dispatchSpy).toHaveBeenCalledWith(removeGender({gender: 'male'}));
  });
});
