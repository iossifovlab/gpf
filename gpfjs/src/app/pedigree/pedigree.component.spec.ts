import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { VariantReportsService } from 'app/variant-reports/variant-reports.service';
import { Observable, of } from 'rxjs';
import { PedigreeComponent } from './pedigree.component';

class MockVariantReportsService {
  public getFamilies(datasetId, groupName, counterId): Observable<string[]> {
    return of(['family1', 'family2', 'family3']);
  }
}

class MockDatasetsService {
  public getSelectedDataset(): object {
    return { id: 'testDataset' };
  }
}

describe('PedigreeComponent', () => {
  let component: PedigreeComponent;
  let fixture: ComponentFixture<PedigreeComponent>;

  beforeEach(async() => {
    await TestBed.configureTestingModule({
      declarations: [PedigreeComponent],
      providers: [
        {provide: VariantReportsService, useValue: new MockVariantReportsService()},
        ConfigService,
        {provide: DatasetsService, useValue: MockDatasetsService},
      ]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(PedigreeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
