import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule, NgModel } from '@angular/forms';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';

import { StudyFilterComponent } from './study-filter.component';

const StudyDescriptorMock: any = {
  studyId: 'id',
  studyName: 'name',
};

const StudyFilterStateMock: any = {
  study: StudyDescriptorMock,
};

describe('StudyFilterComponent', () => {
  let component: StudyFilterComponent;
  let fixture: ComponentFixture<StudyFilterComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [StudyFilterComponent, ErrorsAlertComponent],
      imports: [FormsModule]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(StudyFilterComponent);
    component = fixture.componentInstance;
    component.studyFilterState = StudyFilterStateMock;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
