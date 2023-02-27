import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { PersonFiltersBlockComponent } from './person-filters-block.component';

describe.skip('PersonFiltersBlockComponent', () => {
  let component: PersonFiltersBlockComponent;
  let fixture: ComponentFixture<PersonFiltersBlockComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [PersonFiltersBlockComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(PersonFiltersBlockComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
