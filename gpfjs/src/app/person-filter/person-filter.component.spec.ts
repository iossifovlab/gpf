import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PersonFilterComponent } from './person-filter.component';

describe('PersonFilterComponent', () => {
  let component: PersonFilterComponent;
  let fixture: ComponentFixture<PersonFilterComponent>;

  beforeEach(async() => {
    await TestBed.configureTestingModule({
      imports: [PersonFilterComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(PersonFilterComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
