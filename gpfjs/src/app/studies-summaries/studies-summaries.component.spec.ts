import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { StudiesSummariesComponent } from './studies-summaries.component';

describe('StudiesSummariesComponent', () => {
  let component: StudiesSummariesComponent;
  let fixture: ComponentFixture<StudiesSummariesComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ StudiesSummariesComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(StudiesSummariesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
