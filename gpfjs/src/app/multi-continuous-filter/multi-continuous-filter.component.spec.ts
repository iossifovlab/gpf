import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { MeasuresService } from 'app/measures/measures.service';
import { PhenoMeasureSelectorComponent } from 'app/pheno-measure-selector/pheno-measure-selector.component';
import { UsersService } from 'app/users/users.service';
import { MultiContinuousFilterComponent } from './multi-continuous-filter.component';
import { Component, Input, Output } from '@angular/core';
import { of } from 'rxjs';
import { NgxsModule } from '@ngxs/store';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'gpf-searchable-select',
  template: ''
})
export class SearchableSelectMockComponent {
  @Input() data;
  @Input() caption;
}

const SelectionMock = {
  isEmpty() { return true; }
};

const ContinuousFilterStateMock = {
  id: '',
  type: '',
  role: '',
  from: '',
  source: '',
  sourceType: '',
  selection: SelectionMock,
  isEmpty() { return true; },
  min: 0,
  max: 0,
  domainMin: 0,
  domainMax: 0
};

const PersonFilterMock = {
  name: '',
  from: '',
  source: '',
  sourceType: '',
  role: '',
  filterType: '',
  domain: ['']
};

class MockDatasetsService {
  public getSelectedDataset(): object {
    return { id: 'testDataset' };
  }
}

describe('MultiContinuousFilterComponent', () => {
  let component: MultiContinuousFilterComponent;
  let fixture: ComponentFixture<MultiContinuousFilterComponent>;
  const mockDatasetsService = new MockDatasetsService();

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [
        MultiContinuousFilterComponent,
        PhenoMeasureSelectorComponent,
        SearchableSelectMockComponent,
      ],
      providers: [
        MultiContinuousFilterComponent,
        {provide: MeasuresService, useValue: {getContinuousMeasures: () => of([])}},
        HttpClientTestingModule,
        ConfigService,
        {provide: DatasetsService, useValue: mockDatasetsService},
        UsersService,
      ],
      imports: [
        RouterTestingModule,
        NgxsModule.forRoot([]),
        FormsModule
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MultiContinuousFilterComponent);
    component = fixture.componentInstance;
    component.continuousFilter = PersonFilterMock;
    component.datasetId = '';
    component.continuousFilterState = ContinuousFilterStateMock;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
