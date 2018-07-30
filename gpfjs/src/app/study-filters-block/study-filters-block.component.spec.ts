import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { StudyFiltersBlockComponent } from './study-filters-block.component';

describe('StudyFiltersBlockComponent', () => {
  let component: StudyFiltersBlockComponent;
  let fixture: ComponentFixture<StudyFiltersBlockComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ StudyFiltersBlockComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(StudyFiltersBlockComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
