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
import { GeneSymbolsWithSearchComponent } from '../gene-symbols-with-search/gene-symbols-with-search.component';
import { SearchableSelectComponent } from '../searchable-select/searchable-select.component';
import { FormsModule } from '@angular/forms';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';

class MockActivatedRoute {
  public params = {dataset: 'testDatasetId', get: () => ''};
  public parent = {params: of(this.params)};
  public queryParamMap = of(this.params);
  public snapshot = {params: {gene: 'mockGeneSymbol'}};
}

class MockDatasetsService {
  public getSelectedDataset(): object {
    return { id: 'testDataset', geneBrowser: { domainMax: 100, frequencyColumn: 'testColumn'} };
  }
}

describe('GeneBrowserComponent', () => {
  let component: GeneBrowserComponent;
  let fixture: ComponentFixture<GeneBrowserComponent>;
  const mockDatasetsService = new MockDatasetsService();

  beforeEach(async() => {
    await TestBed.configureTestingModule({
      declarations: [ GeneBrowserComponent, GeneSymbolsWithSearchComponent, SearchableSelectComponent ],
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
    spyOn<any>(component, 'drawDenovoIcons');
    spyOn<any>(component, 'drawTransmittedIcons');
    spyOn<any>(component, 'drawEffectTypesIcons');
    component.filters = null;
    expect(component['drawDenovoIcons']).toHaveBeenCalled();
    expect(component['drawTransmittedIcons']).toHaveBeenCalled();
    expect(component['drawEffectTypesIcons']).toHaveBeenCalled();
  });

  it('should select affected status', () => {
    spyOn<any>(component, 'updateVariants');
    // There are default values to account for, so we use prevLength
    const prevLength = component.summaryVariantsFilter.selectedAffectedStatus.size;
    component.checkAffectedStatus('test', true);
    expect(component.summaryVariantsFilter.selectedAffectedStatus.size).toEqual(prevLength + 1);
    component.checkAffectedStatus('test', false);
    expect(component.summaryVariantsFilter.selectedAffectedStatus.size).toEqual(prevLength);
    expect(component['updateVariants']).toHaveBeenCalledTimes(2);
  });

  it('should select effect type', () => {
    spyOn<any>(component, 'updateVariants');
    const prevLength = component.summaryVariantsFilter.selectedEffectTypes.size;
    component.checkEffectType('test', true);
    expect(component.summaryVariantsFilter.selectedEffectTypes.size).toEqual(prevLength + 1);
    component.checkEffectType('test', false);
    expect(component.summaryVariantsFilter.selectedEffectTypes.size).toEqual(prevLength);
    expect(component['updateVariants']).toHaveBeenCalledTimes(2);
  });

  it('should select variant type', () => {
    spyOn<any>(component, 'updateVariants');
    const prevLength = component.summaryVariantsFilter.selectedVariantTypes.size;
    component.checkVariantType('test', true);
    expect(component.summaryVariantsFilter.selectedVariantTypes.size).toEqual(prevLength + 1);
    component.checkVariantType('test', false);
    expect(component.summaryVariantsFilter.selectedVariantTypes.size).toEqual(prevLength);
    expect(component['updateVariants']).toHaveBeenCalledTimes(2);
  });

  it('should toggle denovo', () => {
    spyOn<any>(component, 'updateVariants');
    component.checkShowDenovo(true);
    expect(component.summaryVariantsFilter.denovo).toEqual(true);
    component.checkShowDenovo(false);
    expect(component.summaryVariantsFilter.denovo).toEqual(false);
    expect(component['updateVariants']).toHaveBeenCalledTimes(2);
  });

  it('should toggle transmitted', () => {
    spyOn<any>(component, 'updateVariants');
    component.checkShowTransmitted(true);
    expect(component.summaryVariantsFilter.transmitted).toEqual(true);
    component.checkShowTransmitted(false);
    expect(component.summaryVariantsFilter.transmitted).toEqual(false);
    expect(component['updateVariants']).toHaveBeenCalledTimes(2);
  });

  it('should set selected region', () => {
    spyOn<any>(component, 'updateVariants');
    component.setSelectedRegion([1, 2]);
    expect(component.summaryVariantsFilter.selectedRegion).toEqual([1, 2]);
    expect(component['updateVariants']).toHaveBeenCalled();
  });

  it('should set selected frequencies', () => {
    spyOn<any>(component, 'updateVariants');
    component.setSelectedFrequencies([3, 4]);
    expect(component.summaryVariantsFilter.selectedFrequencies).toEqual([3, 4]);
    expect(component['updateVariants']).toHaveBeenCalled();
  });

});
