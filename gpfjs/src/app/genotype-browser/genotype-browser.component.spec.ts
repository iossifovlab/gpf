import { ComponentFixture, TestBed } from '@angular/core/testing';
import { GenotypeBrowserComponent } from './genotype-browser.component';
import { QueryService } from 'app/query/query.service';
import { ConfigService } from 'app/config/config.service';
import { RouterTestingModule } from '@angular/router/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { APP_BASE_HREF } from '@angular/common';
import { NgxsModule } from '@ngxs/store';
import { FullscreenLoadingService } from 'app/fullscreen-loading/fullscreen-loading.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { UsersService } from 'app/users/users.service';
import { GenesBlockComponent } from 'app/genes-block/genes-block.component';
import { RegionsBlockComponent } from 'app/regions-block/regions-block.component';
import { GenotypeBlockComponent } from 'app/genotype-block/genotype-block.component';
import { GenomicScoresBlockComponent } from 'app/genomic-scores-block/genomic-scores-block.component';
import { GenomicScoresBlockService } from 'app/genomic-scores-block/genomic-scores-block.service';
import {
  UniqueFamilyVariantsFilterComponent
} from 'app/unique-family-variants-filter/unique-family-variants-filter.component';
import { SaveQueryComponent } from 'app/save-query/save-query.component';
import { NgbNavModule } from '@ng-bootstrap/ng-bootstrap';
import { EffectTypesComponent } from 'app/effect-types/effect-types.component';
import { GenderComponent } from 'app/gender/gender.component';
import { VariantTypesComponent } from 'app/variant-types/variant-types.component';
import { PresentInChildComponent } from 'app/present-in-child/present-in-child.component';
import { PresentInParentComponent } from 'app/present-in-parent/present-in-parent.component';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';
import { CheckboxListComponent, DisplayNamePipe } from 'app/checkbox-list/checkbox-list.component';
import { EffecttypesColumnComponent } from 'app/effect-types/effect-types-column.component';
import { FamilyFiltersBlockComponent } from 'app/family-filters-block/family-filters-block.component';
import { PersonFiltersBlockComponent } from 'app/person-filters-block/person-filters-block.component';
import { FormsModule } from '@angular/forms';
import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { of } from 'rxjs/internal/observable/of';
import { HttpResponse } from '@angular/common/http';
import { Observable } from 'rxjs/internal/Observable';
import { NavigationStart, Router, RouterEvent } from '@angular/router';
import { Subject } from 'rxjs/internal/Subject';
import { Dataset, GenotypeBrowser } from 'app/datasets/datasets';
import { DatasetModel } from 'app/datasets/datasets.state';
import { VariantReportsService } from 'app/variant-reports/variant-reports.service';


const genotypeBrowserConfigMock = {
  personFilters: [],
  familyFilters: [],
  inheritanceTypeFilter: {},
  selectedVariantTypes: {}
};


class MockDatasetsService {
  public getSelectedDataset(): object {
    return { id: 'testDataset', genotypeBrowserConfig: genotypeBrowserConfigMock };
  }
}
class MockQueryService {
  public downloadVariants(): Observable<HttpResponse<Blob>> {
    return of([] as any) as Observable<HttpResponse<Blob>>;
  }

  public cancelStreamPost(): void {
    return null;
  }
}

/* eslint-disable */
const genotypeMock = GenotypeBrowser.fromJson({
  has_pedigree_selector: false,
  has_present_in_child: true,
  has_present_in_parent: false,
  has_present_in_role: false,
  has_family_filters: true,
  has_family_structure_filter: false,
  has_person_filters: true,
  has_study_filters: false,
  has_study_types: false,
  table_columns: [
    {
      name: 'name1',
      source: 'source1',
      format: 'format1'
    },
    {
      name: 'name2',
      source: 'source2',
      format: 'format2'
    }
  ],
  person_filters: [
    {
      name: 'personFilter1',
      from: 'string1',
      source: 'source1',
      source_type: 'sourceType1',
      filter_type: 'filterType1',
      role: 'role1',
    },
    {
      name: 'personFilter2',
      from: 'string2',
      source: 'source2',
      source_type: 'sourceType2',
      filter_type: 'filterType2',
      role: 'role2',
    }
  ],
  family_filters: [
    {
      name: 'familyFilter3',
      from: 'string3',
      source: 'source3',
      source_type: 'sourceType3',
      filter_type: 'filterType3',
      role: 'role3',
    },
    {
      name: 'familyFilter4',
      from: 'string4',
      source: 'source4',
      source_type: 'sourceType4',
      filter_type: 'filterType4',
      role: 'role4',
    }
  ],
  inheritance_type_filter: ['inheritance', 'string1'],
  selected_inheritance_type_filter_values: ['selectedInheritance', 'string2'],
  variant_types: ['variant', 'string3'],
  selected_variant_types: ['selectedVariant', 'string1'],
  max_variants_count: 5,
});
/* eslint-enable */

describe('GenotypeBrowserComponent', () => {
  let component: GenotypeBrowserComponent;
  let fixture: ComponentFixture<GenotypeBrowserComponent>;
  const queryService = new MockQueryService();
  let loadingService: FullscreenLoadingService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [
        GenotypeBrowserComponent,
        GenotypeBlockComponent,
        GenomicScoresBlockComponent,
        SaveQueryComponent,
        PresentInChildComponent,
        PresentInParentComponent,
        ErrorsAlertComponent,
        CheckboxListComponent,
        EffecttypesColumnComponent,
        FamilyFiltersBlockComponent,
        PersonFiltersBlockComponent,
        DisplayNamePipe
      ],
      providers: [
        {provide: QueryService, useValue: queryService},
        ConfigService,
        FullscreenLoadingService,
        UsersService,
        VariantReportsService,
        GenomicScoresBlockService,
        { provide: DatasetsService, useValue: new MockDatasetsService() },
        UniqueFamilyVariantsFilterComponent,
        EffectTypesComponent,
        GenderComponent,
        VariantTypesComponent,
        GenesBlockComponent,
        RegionsBlockComponent,
        { provide: APP_BASE_HREF, useValue: '' }
      ],
      imports: [
        HttpClientTestingModule, RouterTestingModule, NgbNavModule, FormsModule,
        NgxsModule.forRoot([], {developmentMode: true}),
      ],
      schemas: [CUSTOM_ELEMENTS_SCHEMA]
    }).compileComponents();
    fixture = TestBed.createComponent(GenotypeBrowserComponent);
    component = fixture.componentInstance;
    loadingService = TestBed.inject(FullscreenLoadingService);

    // eslint-disable-next-line max-len
    const selectedDatasetMock = new Dataset('testId', 'desc', '', 'testDataset', [], true, [], [], [], '', true, true, true, true, null, genotypeMock, null, [], null, null, '', null);
    const selectedDatasetMockModel: DatasetModel = {selectedDataset: selectedDatasetMock};

    component['store'] = {
      selectOnce: () => of(selectedDatasetMockModel)
    } as never;

    fixture.detectChanges();
  });

  it('should create', () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  it('should test download', () => {
    const mockEvent = {
      target: {
        queryData: {
          value: ''
        },
        submit: jest.fn()
      }
    };
    component.onSubmit(mockEvent);
    expect(mockEvent.target.queryData.value).toStrictEqual(JSON.stringify({
      datasetId: component.selectedDataset.id,
      download: true
    }));
    expect(mockEvent.target.submit).toHaveBeenCalledTimes(1);
  });

  it('should cancel queries on router change', () => {
    const stopSpy = jest.spyOn(loadingService, 'setLoadingStop');
    const cancelSpy = jest.spyOn(queryService, 'cancelStreamPost');
    const router = TestBed.inject(Router);

    (router.events as Subject<RouterEvent>).next(new NavigationStart(1, 'start'));

    expect(stopSpy).toHaveBeenCalledTimes(1);
    expect(cancelSpy).toHaveBeenCalledTimes(1);
  });
});
