import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { NgxsModule } from '@ngxs/store';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';

import { FamilyIdsComponent } from './family-ids.component';
import { FamilyIdsState } from './family-ids.state';

describe('FamilyIdsComponent', () => {
  let component: FamilyIdsComponent;
  let fixture: ComponentFixture<FamilyIdsComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [FamilyIdsComponent, ErrorsAlertComponent],
      imports: [FormsModule, NgxsModule.forRoot([FamilyIdsState], {developmentMode: true})]
    }).compileComponents();

    fixture = TestBed.createComponent(FamilyIdsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
