import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { SortingButtonsComponent } from './sorting-buttons.component';

describe('SortingButtonsComponent', () => {
  let component: SortingButtonsComponent;
  let fixture: ComponentFixture<SortingButtonsComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ SortingButtonsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SortingButtonsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
