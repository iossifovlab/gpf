import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { MultiContinuousFilterComponent } from './multi-continuous-filter.component';

describe('MultiContinuousFilterComponent', () => {
  let component: MultiContinuousFilterComponent;
  let fixture: ComponentFixture<MultiContinuousFilterComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ MultiContinuousFilterComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MultiContinuousFilterComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
