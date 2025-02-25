import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PersonFilterComponent } from './person-filter.component';
import { StoreModule } from '@ngrx/store';
import { MeasureHistogram } from 'app/measures/measures';
import { NumberHistogram } from 'app/utils/histogram-types';

describe('PersonFilterComponent', () => {
  let component: PersonFilterComponent;
  let fixture: ComponentFixture<PersonFilterComponent>;

  beforeEach(async() => {
    await TestBed.configureTestingModule({
      declarations: [PersonFilterComponent],
      imports: [StoreModule.forRoot()],
    }).compileComponents();

    fixture = TestBed.createComponent(PersonFilterComponent);
    component = fixture.componentInstance;

    component.selectedMeasure = new MeasureHistogram(
      'm1',
      new NumberHistogram([1, 2], [4, 5], 'larger1', 'smaller1', 7, 8, true, true)
    );
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
