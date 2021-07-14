/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { GenderComponent } from './gender.component';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';
import { NgxsModule } from '@ngxs/store';
import { of } from 'rxjs';

describe('GenderComponent', () => {
  let component: GenderComponent;
  let fixture: ComponentFixture<GenderComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [GenderComponent, ErrorsAlertComponent],
      imports: [NgxsModule.forRoot([])]
    })
      .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(GenderComponent);
    component = fixture.componentInstance;
    component['store'] = {
      selectOnce(f) {
        return of({genders: ['male', 'female']});
      },
      dispatch(set) {}
    } as any;
    fixture.detectChanges();
  });

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

});
