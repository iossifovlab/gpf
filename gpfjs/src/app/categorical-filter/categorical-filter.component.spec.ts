import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { CategoricalFilterComponent } from './categorical-filter.component';

describe('CategoricalFilterComponent', () => {
  let component: CategoricalFilterComponent;
  let fixture: ComponentFixture<CategoricalFilterComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ CategoricalFilterComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CategoricalFilterComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
