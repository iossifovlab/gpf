import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { NgxsModule } from '@ngxs/store';
import { PersonIdsState } from './person-ids.state';

import { PersonIdsComponent } from './person-ids.component';

describe('PersonIdsComponent', () => {
  let component: PersonIdsComponent;
  let fixture: ComponentFixture<PersonIdsComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ PersonIdsComponent ],
      imports: [ FormsModule, NgxsModule.forRoot([PersonIdsState])],
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
