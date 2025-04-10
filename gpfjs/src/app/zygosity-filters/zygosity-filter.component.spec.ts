import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ZygosityFilterComponent } from './zygosity-filter.component';
import { zygosityFilterReducer } from './zygosity-filter.state';
import { StoreModule } from '@ngrx/store';

describe('ZygosityFiltersComponent', () => {
  let component: ZygosityFilterComponent;
  let fixture: ComponentFixture<ZygosityFilterComponent>;

  beforeEach(async() => {
    await TestBed.configureTestingModule({
      declarations: [ZygosityFilterComponent],
      imports: [
        StoreModule.forRoot({zygosityFilter: zygosityFilterReducer})
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ZygosityFilterComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
