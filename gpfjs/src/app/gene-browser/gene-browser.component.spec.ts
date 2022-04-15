import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { NgxsModule } from '@ngxs/store';
import { of } from 'rxjs';
import { GeneSymbolsState } from 'app/gene-symbols/gene-symbols.state';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { FullscreenLoadingService } from 'app/fullscreen-loading/fullscreen-loading.service';
import { QueryService } from 'app/query/query.service';
import { UsersService } from 'app/users/users.service';
import { GeneService } from './gene.service';
import { GeneBrowserComponent } from './gene-browser.component';
import { SearchableSelectComponent } from '../searchable-select/searchable-select.component';
import { FormsModule } from '@angular/forms';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { SummaryAllelesFilter } from './summary-variants';

jest.mock('../utils/svg-drawing');

class MockActivatedRoute {
  public params = {dataset: 'testDatasetId', get: () => ''};
  public parent = {params: of(this.params)};
  public queryParamMap = of(this.params);
  public snapshot = {params: {gene: 'mockGeneSymbol'}};
}

class MockDatasetsService {
  public getSelectedDataset(): object {
    return {
      id: 'testDataset',
      geneBrowser: { domainMax: 100, frequencyColumn: 'testColumn'},
      personSetCollections: { getLegend: () => [] },
    };
  }
}

describe('GeneBrowserComponent', () => {
  let component: GeneBrowserComponent;
  let fixture: ComponentFixture<GeneBrowserComponent>;
  const mockDatasetsService = new MockDatasetsService();

  beforeEach(async() => {
    await TestBed.configureTestingModule({
      declarations: [ GeneBrowserComponent, SearchableSelectComponent ],
      providers: [
        ConfigService, {provide: ActivatedRoute, useValue: new MockActivatedRoute()},
        QueryService, UsersService, GeneService, {provide: DatasetsService, useValue: mockDatasetsService},
        FullscreenLoadingService,
      ],
      imports: [
        HttpClientTestingModule, RouterTestingModule, NgxsModule.forRoot([GeneSymbolsState]), NgbModule, FormsModule
      ],
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(GeneBrowserComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should draw legend on filters div set', () => {
    expect(component).toBeTruthy();
    jest.spyOn<any, any>(component, 'drawDenovoIcons').mockImplementation(() => {});
    jest.spyOn<any, any>(component, 'drawTransmittedIcons').mockImplementation(() => {});
    jest.spyOn<any, any>(component, 'drawEffectTypesIcons').mockImplementation(() => {});
    component.filters = null;
    expect(component['drawDenovoIcons']).toHaveBeenCalled();
    expect(component['drawTransmittedIcons']).toHaveBeenCalled();
    expect(component['drawEffectTypesIcons']).toHaveBeenCalled();
  });

  it('should select affected status', () => {
    // There are default values to account for, so we use prevLength
    const prevLength = component.summaryVariantsFilter.selectedAffectedStatus.size;
    component.checkAffectedStatus('test', true);
    expect(component.summaryVariantsFilter.selectedAffectedStatus.size).toEqual(prevLength + 1);
    component.checkAffectedStatus('test', false);
    expect(component.summaryVariantsFilter.selectedAffectedStatus.size).toEqual(prevLength);
  });

  it('should select effect type', () => {
    const prevLength = component.summaryVariantsFilter.selectedEffectTypes.size;
    component.checkEffectType('test', true);
    expect(component.summaryVariantsFilter.selectedEffectTypes.size).toEqual(prevLength + 1);
    component.checkEffectType('test', false);
    expect(component.summaryVariantsFilter.selectedEffectTypes.size).toEqual(prevLength);
  });

  it('should select variant type', () => {
    const prevLength = component.summaryVariantsFilter.selectedVariantTypes.size;
    component.checkVariantType('test', true);
    expect(component.summaryVariantsFilter.selectedVariantTypes.size).toEqual(prevLength + 1);
    component.checkVariantType('test', false);
    expect(component.summaryVariantsFilter.selectedVariantTypes.size).toEqual(prevLength);
  });

  it('should toggle denovo', () => {
    component.checkShowDenovo(true);
    expect(component.summaryVariantsFilter.denovo).toEqual(true);
    component.checkShowDenovo(false);
    expect(component.summaryVariantsFilter.denovo).toEqual(false);
  });

  it('should toggle transmitted', () => {
    component.checkShowTransmitted(true);
    expect(component.summaryVariantsFilter.transmitted).toEqual(true);
    component.checkShowTransmitted(false);
    expect(component.summaryVariantsFilter.transmitted).toEqual(false);
  });

  it('should set selected region', () => {
    jest.spyOn<any, any>(component, 'updateVariants').mockImplementation(() => {});
    component.setSelectedRegion([1, 2]);
    expect(component.summaryVariantsFilter.selectedRegion).toEqual([1, 2]);
    expect(component['updateVariants']).toHaveBeenCalled();
  });

  it('should set selected frequencies', () => {
    jest.spyOn<any, any>(component, 'updateVariants').mockImplementation(() => {});
    component.setSelectedFrequencies([3, 4]);
    expect(component.summaryVariantsFilter.selectedFrequencies).toEqual([3, 4]);
    expect(component['updateVariants']).toHaveBeenCalled();
  });

  it('should toggle CNV effects properly if "Other" effect type is selected', () => {
    component.summaryVariantsFilter = new SummaryAllelesFilter(true, true, false);
    component.effectTypeValues.forEach(eff => component.checkEffectType(eff, true));
    expect(component.summaryVariantsFilter.queryParams['effectTypes']).toEqual([
      'frame-shift', 'nonsense', 'splice-site','no-frame-shift-newStop',
      'missense', 'synonymous', 'CNV+', 'CNV-', '3\'UTR', '3\'UTR-intron', '5\'UTR', '5\'UTR-intron',
      'intergenic', 'intron', 'no-frame-shift', 'noEnd', 'noStart', 'non-coding', 'non-coding-intron', 'CDS',
    ]);

    component.checkEffectType('Other', false);
    expect(component.summaryVariantsFilter.queryParams['effectTypes']).toEqual([
      'frame-shift', 'nonsense', 'splice-site','no-frame-shift-newStop',
      'missense', 'synonymous', 'CNV+', 'CNV-'
    ]);
  });
});
