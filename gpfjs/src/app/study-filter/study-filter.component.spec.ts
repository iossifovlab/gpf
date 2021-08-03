import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';

import { StudyFilterComponent } from './study-filter.component';

const studyDescriptorMock: any = {
  studyId: 'id',
  studyName: 'name',
};

describe('StudyFilterComponent', () => {
  let component: StudyFilterComponent;
  let fixture: ComponentFixture<StudyFilterComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [StudyFilterComponent, ErrorsAlertComponent],
      imports: [FormsModule]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(StudyFilterComponent);
    component = fixture.componentInstance;
    component.selectedStudy = studyDescriptorMock;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
