import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { of } from 'rxjs';
import { StudyFiltersComponent } from './study-filters.component';
import { NgbNavModule, NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { RemoveButtonComponent } from 'app/remove-button/remove-button.component';
import { AddButtonComponent } from 'app/add-button/add-button.component';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';
import { FormsModule } from '@angular/forms';
import { DatasetsComponent } from 'app/datasets/datasets.component';
import { UsersService } from 'app/users/users.service';
import { ConfigService } from 'app/config/config.service';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { APP_BASE_HREF } from '@angular/common';
import { DatasetsService } from 'app/datasets/datasets.service';
import { RouterModule } from '@angular/router';
import { DatasetNode } from 'app/dataset-node/dataset-node';
import { DatasetsTreeService } from 'app/datasets/datasets-tree.service';
import { Store, StoreModule } from '@ngrx/store';
import { studyTypesReducer } from 'app/study-types/study-types.state';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const datasetConfigMock: any = {
  studies: ['test_name1', 'test_name2']
};

class DatasetsComponentMock {
  public datasets = {datasetTrees: [DatasetNode]};
}

describe('StudyFiltersComponent', () => {
  let component: StudyFiltersComponent;
  let fixture: ComponentFixture<StudyFiltersComponent>;
  let store: Store;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [
        StudyFiltersComponent,
        RemoveButtonComponent,
        AddButtonComponent,
        ErrorsAlertComponent
      ],
      providers: [
        NgbNavModule, NgbModule, FormsModule,
        {provide: DatasetsComponent, useValue: DatasetsComponentMock},
        UsersService, ConfigService, { provide: APP_BASE_HREF, useValue: '' },
        DatasetsService, DatasetsTreeService
      ],
      imports: [
        NgbNavModule, NgbModule, FormsModule,
        StoreModule.forRoot({studyFilters: studyTypesReducer}), HttpClientTestingModule,
        RouterModule.forRoot([])
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(StudyFiltersComponent);
    component = fixture.componentInstance;

    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    store = TestBed.inject(Store);
    jest.spyOn(store, 'select').mockReturnValue(of({}));
    jest.spyOn(store, 'dispatch').mockReturnValue();

    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    component.dataset = datasetConfigMock;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
