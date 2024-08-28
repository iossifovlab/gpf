import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { ConfigService } from 'app/config/config.service';
import { VariantReportsService } from 'app/variant-reports/variant-reports.service';
import { Observable, of } from 'rxjs';
import { PedigreeComponent } from './pedigree.component';
import { DatasetModel } from 'app/datasets/datasets.state';
import { Store, StoreModule } from '@ngrx/store';

class MockVariantReportsService {
  public getFamilies(): Observable<string[]> {
    return of(['family1', 'family2', 'family3']);
  }
}


describe('PedigreeComponent', () => {
  let component: PedigreeComponent;
  let fixture: ComponentFixture<PedigreeComponent>;
  let modalService: NgbModal;
  let store: Store;
  const mockVariantReportsService = new MockVariantReportsService();

  beforeEach(async() => {
    await TestBed.configureTestingModule({
      declarations: [PedigreeComponent],
      providers: [
        {provide: VariantReportsService, useValue: mockVariantReportsService},
        ConfigService,
      ],
      imports: [StoreModule.forRoot({})]
    }).compileComponents();

    modalService = TestBed.inject(NgbModal);
    fixture = TestBed.createComponent(PedigreeComponent);
    component = fixture.componentInstance;

    const selectedDatasetMockModel: DatasetModel = {selectedDatasetId: 'testId'};

    store = TestBed.inject(Store);
    jest.spyOn(store, 'select').mockReturnValue(of(selectedDatasetMockModel));

    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have working return guard in the loadFamilyListData() function', () => {
    const getFamiliesSpy = jest.spyOn(mockVariantReportsService, 'getFamilies');

    component.familyIdsList = ['1', '2', '3'];
    component.loadFamilyListData();
    expect(getFamiliesSpy).not.toHaveBeenCalled();

    component.familyIdsList = undefined;
    component.loadFamilyListData();
    expect(getFamiliesSpy).toHaveBeenCalled();
  });

  it('should open modal', () => {
    jest.spyOn(modalService, 'open');
    jest.spyOn(component, 'loadFamilyListData');
    component.openModal();
    expect(modalService.open).toHaveBeenCalled();
  });
});
