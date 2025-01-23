import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CategoricalValuesDropdownComponent } from './categorical-values-dropdown.component';

describe('CategoricalValuesDropdownComponent', () => {
  let component: CategoricalValuesDropdownComponent;
  let fixture: ComponentFixture<CategoricalValuesDropdownComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CategoricalValuesDropdownComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CategoricalValuesDropdownComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
