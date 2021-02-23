import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { PersonIdsComponent } from './person-ids.component';

describe('PersonIdsComponent', () => {
  let component: PersonIdsComponent;
  let fixture: ComponentFixture<PersonIdsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PersonIdsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PersonIdsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
