import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { ConfigService } from 'app/config/config.service';
import { VariantReportsService } from 'app/variant-reports/variant-reports.service';
import { Observable, of } from 'rxjs';
import { PedigreeComponent } from './pedigree.component';
import { NgxsModule } from '@ngxs/store';
import { Dataset } from 'app/datasets/datasets';
import { DatasetModel } from 'app/datasets/datasets.state';

class MockVariantReportsService {
  public getFamilies(): Observable<string[]> {
    return of(['family1', 'family2', 'family3']);
  }
}


describe('PedigreeComponent', () => {
  let component: PedigreeComponent;
  let fixture: ComponentFixture<PedigreeComponent>;
  let modalService: NgbModal;
  const mockVariantReportsService = new MockVariantReportsService();

  beforeEach(async() => {
    await TestBed.configureTestingModule({
      declarations: [PedigreeComponent],
      providers: [
        {provide: VariantReportsService, useValue: mockVariantReportsService},
        ConfigService,
      ],
      imports: [NgxsModule.forRoot([], {developmentMode: true})]
    }).compileComponents();

    modalService = TestBed.inject(NgbModal);
    fixture = TestBed.createComponent(PedigreeComponent);
    component = fixture.componentInstance;

    // eslint-disable-next-line max-len
    const selectedDatasetMock = new Dataset('testId', 'desc', '', 'testDataset', [], true, [], [], [], '', true, true, true, true, null, null, null, [], null, null, '', null);
    const selectedDatasetMockModel: DatasetModel = {selectedDataset: selectedDatasetMock};

    component['store'] = {
      selectOnce: () => of(selectedDatasetMockModel)
    } as never;

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
