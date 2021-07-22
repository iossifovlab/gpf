import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { PersonIdsComponent } from './person-ids.component';

describe('PersonIdsComponent', () => {
  let component: PersonIdsComponent;
  let fixture: ComponentFixture<PersonIdsComponent>;

  beforeEach(waitForAsync(() => {
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
