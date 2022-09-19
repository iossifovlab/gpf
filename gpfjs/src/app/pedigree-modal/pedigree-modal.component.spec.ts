import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { VariantReportsService } from 'app/variant-reports/variant-reports.service';
import { Observable, of } from 'rxjs';
import { PedigreeModalComponent } from './pedigree-modal.component';

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

describe('PedigreeModalComponent', () => {
  let component: PedigreeModalComponent;
  let fixture: ComponentFixture<PedigreeModalComponent>;

  beforeEach(async() => {
    await TestBed.configureTestingModule({
      declarations: [PedigreeModalComponent],
      providers: [
        {provide: VariantReportsService, useValue: new MockVariantReportsService()},
        ConfigService,
        {provide: DatasetsService, useValue: MockDatasetsService},
      ]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(PedigreeModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
