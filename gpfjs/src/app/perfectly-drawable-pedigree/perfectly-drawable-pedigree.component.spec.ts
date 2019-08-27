import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { PerfectlyDrawablePedigreeComponent } from './perfectly-drawable-pedigree.component';

describe('PerfectlyDrawablePedigreeComponent', () => {
  let component: PerfectlyDrawablePedigreeComponent;
  let fixture: ComponentFixture<PerfectlyDrawablePedigreeComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PerfectlyDrawablePedigreeComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PerfectlyDrawablePedigreeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
