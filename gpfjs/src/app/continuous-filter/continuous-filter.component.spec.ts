import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ContinuousFilterComponent } from './continuous-filter.component';

describe('ContinuousFilterComponent', () => {
  let component: ContinuousFilterComponent;
  let fixture: ComponentFixture<ContinuousFilterComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ContinuousFilterComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ContinuousFilterComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
