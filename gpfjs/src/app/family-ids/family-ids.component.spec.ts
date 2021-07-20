import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { NgxsModule } from '@ngxs/store';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';

import { FamilyIdsComponent } from './family-ids.component';
import { FamilyIdsState } from './family-ids.state';

describe('FamilyIdsComponent', () => {
  let component: FamilyIdsComponent;
  let fixture: ComponentFixture<FamilyIdsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [FamilyIdsComponent, ErrorsAlertComponent],
      imports: [FormsModule, NgxsModule.forRoot([FamilyIdsState])]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(FamilyIdsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
