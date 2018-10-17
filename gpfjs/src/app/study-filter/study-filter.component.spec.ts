import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { StudyFilterComponent } from './study-filter.component';

describe('StudyFilterComponent', () => {
  let component: StudyFilterComponent;
  let fixture: ComponentFixture<StudyFilterComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ StudyFilterComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(StudyFilterComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
