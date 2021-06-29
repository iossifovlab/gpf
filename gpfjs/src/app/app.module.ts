import { BrowserModule } from '@angular/platform-browser';
import { NgModule, Injector, ErrorHandler } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';

import { NgbModule } from '@ng-bootstrap/ng-bootstrap';

import { AppComponent } from './app.component';

import { DatasetsService } from './datasets/datasets.service';
import { ConfigService } from './config/config.service';
import { GenderComponent } from './gender/gender.component';
import { PresentInChildComponent } from './present-in-child/present-in-child.component';
import { PresentInChildState } from './present-in-child/present-in-child.state';
import { PresentInParentComponent } from './present-in-parent/present-in-parent.component';
import { VarianttypesComponent } from './varianttypes/varianttypes.component';
import { EffecttypesComponent } from './effecttypes/effecttypes.component';
import { EffecttypesColumnComponent } from './effecttypes/effecttypes-column.component';
import { GenotypePreviewTableComponent } from './genotype-preview-table/genotype-preview-table.component';
import { QueryService } from './query/query.service';

import { GpfTableModule } from './table/table.module';
import { DatasetsComponent } from './datasets/datasets.component';
import { PedigreeSelectorComponent } from './pedigree-selector/pedigree-selector.component';
import { GenotypeBlockComponent } from './genotype-block/genotype-block.component';
import { GenesBlockComponent } from './genes-block/genes-block.component';
import { GeneSymbolsComponent } from './gene-symbols/gene-symbols.component';
import { GeneSymbolsState } from './gene-symbols/gene-symbols.state';
import { RegionsFilterComponent } from './regions-filter/regions-filter.component';
import { RegionsBlockComponent } from './regions-block/regions-block.component';
import { PedigreeChartModule } from './pedigree-chart/pedigree-chart.module';

import { HistogramModule } from './histogram/histogram.module';
import { GeneWeightsComponent } from './gene-weights/gene-weights.component';
import { GeneWeightsService } from './gene-weights/gene-weights.service';

import { GeneSetsComponent } from './gene-sets/gene-sets.component';
import { GeneSetsService } from './gene-sets/gene-sets.service';

import { SearchableSelectComponent } from './searchable-select/searchable-select.component';
import { SearchableSelectTemplateDirective } from './searchable-select/searchable-select-template.directive';

import { UsersComponent } from './users/users.component';
import { UsersService } from './users/users.service';

import { BoldMatchingPipe } from './utils/bold-matching.pipe';
import { MinValidatorDirective, MaxValidatorDirective } from './utils/min-max.validator';

import { StudyTypesComponent } from './study-types/study-types.component';
import { StudyTypesState } from './study-types/study-types.state';

import { CookieService} from 'ngx-cookie-service';

import { GenotypeBrowserComponent } from './genotype-browser/genotype-browser.component';

import { EnrichmentToolComponent } from './enrichment-tool/enrichment-tool.component';
import { EnrichmentModelsBlockComponent } from './enrichment-models-block/enrichment-models-block.component';
import { EnrichmentModelsComponent } from './enrichment-models/enrichment-models.component';
import { EnrichmentModelsService } from './enrichment-models/enrichment-models.service';
import { EnrichmentQueryService } from './enrichment-query/enrichment-query.service';
import { EnrichmentTableComponent } from './enrichment-table/enrichment-table.component';
import { EnrichmentTableRowComponent } from './enrichment-table/enrichment-table-row.component';

import { FullscreenLoadingComponent } from './fullscreen-loading/fullscreen-loading.component';
import { FullscreenLoadingService } from './fullscreen-loading/fullscreen-loading.service';

import { EncodeUriComponentPipe } from './utils/encode-uri-component.pipe';

import { RouteReuseStrategy, RouterModule, Routes } from '@angular/router';
import { TaggingRouteReuseStrategy } from 'app/route-reuse.strategy';

import { StateRestoreService } from './store/state-restore.service';
import { PersonFiltersComponent } from './person-filters/person-filters.component';
import { FamilyFiltersBlockComponent } from './family-filters-block/family-filters-block.component';
import { ContinuousFilterComponent } from './continuous-filter/continuous-filter.component';
import { MultiContinuousFilterComponent } from './multi-continuous-filter/multi-continuous-filter.component';
import { CategoricalFilterComponent } from './categorical-filter/categorical-filter.component';
import { MeasuresService } from './measures/measures.service';
import { FamilyIdsComponent } from './family-ids/family-ids.component';
import { FamilyIdsState } from './family-ids/family-ids.state';

import { NumberWithExpPipe } from './utils/number-with-exp.pipe';
import { PhenoToolComponent } from './pheno-tool/pheno-tool.component';
import { PhenoMeasureSelectorComponent } from './pheno-measure-selector/pheno-measure-selector.component';
import { PhenoToolMeasureComponent } from './pheno-tool-measure/pheno-tool-measure.component';
import { PhenoToolGenotypeBlockComponent } from './pheno-tool-genotype-block/pheno-tool-genotype-block.component';
import { PhenoToolService } from './pheno-tool/pheno-tool.service';
import { PhenoToolResultsChartComponent } from './pheno-tool-results-chart/pheno-tool-results-chart.component';
import { PhenoToolResultsChartPerEffectComponent } from './pheno-tool-results-chart/pheno-tool-results-chart-per-effect.component';
import { PhenoToolResultsChartPerResultComponent } from './pheno-tool-results-chart/pheno-tool-results-chart-per-result.component';
import { PhenoToolEffectTypesComponent } from './pheno-tool-effect-types/pheno-tool-effect-types.component';

import { FamilyCountersComponent } from './family-counters/family-counters.component';
import { FamilyCountersService } from './family-counters/family-counters.service';
import { RegistrationComponent } from './registration/registration.component';
import { ForgotPasswordComponent } from './forgot-password/forgot-password.component';
import { PhenoBrowserComponent } from './pheno-browser/pheno-browser.component';
import { PhenoBrowserService } from './pheno-browser/pheno-browser.service';
import { ResetPasswordComponent } from './reset-password/reset-password.component';
import { PhenoBrowserModalContentComponent } from './pheno-browser-modal-content/pheno-browser-modal-content.component';
import { PhenoBrowserTableComponent } from './pheno-browser-table/pheno-browser-table.component';

import { PValueIntensityPipe } from './utils/p-value-intensity.pipe';

import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { VariantReportsComponent } from './variant-reports/variant-reports.component';
import { VariantReportsService } from './variant-reports/variant-reports.service';
import { DatasetDescriptionComponent } from './dataset-description/dataset-description.component';

import { GenomicScoresComponent } from './genomic-scores/genomic-scores.component';
import { GenomicScoresBlockComponent } from './genomic-scores-block/genomic-scores-block.component';
import { GenomicScoresBlockService } from './genomic-scores-block/genomic-scores-block.service';

import { MarkdownModule } from 'ngx-markdown';
import { UserManagementComponent } from './user-management/user-management.component';
import { UserInfoPipe } from './users/user-info.pipe';
import { UsersTableComponent } from './users-table/users-table.component';
import { GroupsTableComponent } from './groups-table/groups-table.component';
import { UserEditComponent } from './user-edit/user-edit.component';
import { ManagementComponent } from './management/management.component';
import { UsersGroupsService } from './users-groups/users-groups.service';

import { ConfirmationPopoverModule } from 'angular-confirmation-popover';
import { UserCreateComponent } from './user-create/user-create.component';
import { GroupsBulkAddComponent } from './groups-bulk-add/groups-bulk-add.component';
import { GroupsBulkRemoveComponent } from './groups-bulk-remove/groups-bulk-remove.component';
import { UserGroupsSelectorComponent } from './user-groups-selector/user-groups-selector.component';
import { UsersActionsComponent } from './users-actions/users-actions.component';
import { DatasetsTableComponent } from './datasets-table/datasets-table.component';
import { GenotypeBrowserSingleViewComponent } from './genotype-browser-single-view/genotype-browser-single-view.component';
import { GenotypePreviewFieldComponent } from './genotype-preview-field/genotype-preview-field.component';
import { ErrorsAlertComponent } from './errors-alert/errors-alert.component';
import { SmallRemoveButtonComponent } from './small-remove-button/small-remove-button.component';
import { ShareQueryButtonComponent } from './share-query-button/share-query-button.component';
import { LoadQueryComponent } from './load-query/load-query.component';
import { PerfectlyDrawablePedigreeComponent } from './perfectly-drawable-pedigree/perfectly-drawable-pedigree.component';
import { PedigreeMockService } from './perfectly-drawable-pedigree/pedigree-mock.service';
import { NonPdpPedigreesComponent } from './non-pdp-pedigrees/non-pdp-pedigrees.component';
import { PerfectlyDrawablePedigreeService } from './perfectly-drawable-pedigree/perfectly-drawable-pedigree.service';
import { StudyFiltersBlockComponent } from './study-filters-block/study-filters-block.component';
import { StudyFilterComponent } from './study-filter/study-filter.component';
import { AddButtonComponent } from './add-button/add-button.component';
import { RemoveButtonComponent } from './remove-button/remove-button.component';
import { PopupComponent } from './popup/popup.component';
import { PresentInRoleComponent } from './present-in-role/present-in-role.component';
import { SaveQueryComponent } from './save-query/save-query.component';
import { SavedQueriesTableComponent } from './saved-queries-table/saved-queries-table.component';
import { SavedQueriesComponent } from './saved-queries/saved-queries.component';
import { InheritancetypesComponent } from './inheritancetypes/inheritancetypes.component';
import { InheritancetypesState } from './inheritancetypes/inheritancetypes.state';
import { GeneBrowserComponent } from './gene-browser/gene-browser.component';
import { GlobalErrorHandler } from './global-error-handler/global-error-handler';
import { GlobalErrorDisplayComponent } from './global-error-display/global-error-display.component';
import { NgMultiSelectDropDownModule } from 'ng-multiselect-dropdown';
import { DatasetPermissionGuard } from './dataset-permission.guard';
import { CommonReportsRowComponent } from './variant-reports/common-reports-row/common-reports-row.component';
import { CommonReportsPedigreeCellComponent } from './variant-reports/common-reports-pedigree-cell/common-reports-pedigree-cell.component';
import { GeneViewComponent } from './gene-view/gene-view.component';
import { GeneSymbolsWithSearchComponent } from './gene-symbols-with-search/gene-symbols-with-search.component';
import { LoadingSpinnerComponent } from './loading-spinner/loading-spinner.component';
import { DatasetNodeComponent } from './dataset-node/dataset-node.component';
import { AutismGeneProfilesTableComponent } from './autism-gene-profiles-table/autism-gene-profiles-table.component';
import { MultipleSelectMenuComponent } from './multiple-select-menu/multiple-select-menu.component';
import { Ng2SearchPipeModule } from 'ng2-search-filter';
import { AutismGeneProfilesBlockComponent } from './autism-gene-profiles-block/autism-gene-profiles-block.component';
import { AutismGeneProfileSingleViewComponent } from './autism-gene-profiles-single-view/autism-gene-profile-single-view.component';
import { MiddleClickDirective } from './autism-gene-profiles-table/middle-click.directive';
import { PersonFiltersBlockComponent } from './person-filters-block/person-filters-block.component';
import { PersonIdsComponent } from './person-ids/person-ids.component';
import { PersonIdsState } from './person-ids/person-ids.state';
import { FamilyTypeFilterComponent } from './family-type-filter/family-type-filter.component';
import { SortingButtonsComponent } from './sorting-buttons/sorting-buttons.component';
import { BnNgIdleService } from 'bn-ng-idle';
import { AutismGeneProfileSingleViewWrapperComponent } from './autism-gene-profile-single-view-wrapper/autism-gene-profile-single-view-wrapper.component';
import { NgxsModule } from '@ngxs/store';
import { VarianttypesState } from './varianttypes/varianttypes.state';
import { EffecttypesState } from './effecttypes/effecttypes.state';
import { GenderState } from './gender/gender.state';
import { RegionsFilterState } from './regions-filter/regions-filter.state';
import { CheckboxListComponent } from './checkbox-list/checkbox-list.component';

const appRoutes: Routes = [
  {
    path: 'datasets',
    component: DatasetsComponent
  },
  {
    path: 'datasets/:dataset',
    component: DatasetsComponent,
    data: {
      reuse: false
    },
    canLoad: [DatasetPermissionGuard],
    children: [
      {
        path: 'genotype-browser',
        component: GenotypeBrowserSingleViewComponent
      },
      {
        path: 'enrichment-tool',
        component: EnrichmentToolComponent
      },
      {
        path: 'phenotype-tool',
        component: PhenoToolComponent
      },
      {
        path: 'phenotype-browser',
        component: PhenoBrowserComponent
      },
      {
        path: 'dataset-description',
        component: DatasetDescriptionComponent
      },
      {
        path: 'dataset-statistics',
        component: VariantReportsComponent
      },
      {
        path: 'gene-browser',
        component: GeneBrowserComponent
      },
      {
        path: 'gene-browser/:gene',
        component: GeneBrowserComponent
      }
    ]
  },
  {
    path: 'autism-gene-profiles',
    component: AutismGeneProfilesBlockComponent
  },
  {
    path: 'autism-gene-profiles/:gene',
    component: AutismGeneProfileSingleViewWrapperComponent
  },
  {
    path: 'management',
    component: ManagementComponent,
    children: [
      {
        path: '',
        pathMatch: 'full',
        component: UserManagementComponent
      },
      {
        path: 'users/create',
        component: UserCreateComponent
      },
      {
        path: 'users/add-group',
        component: GroupsBulkAddComponent
      },
      {
        path: 'users/remove-group',
        component: GroupsBulkRemoveComponent
      },
      {
        path: 'users/:id',
        component: UserEditComponent
      }
    ]
  },
  {
    path: 'validate/:validateString',
    component: ResetPasswordComponent,
  },
  {
    path: 'load-query/:uuid',
    component: LoadQueryComponent
  },
  {
    path: 'saved-queries',
    component: SavedQueriesComponent
  },
  {
    path: '**',
    redirectTo: 'datasets'
  },
];


@NgModule({
  declarations: [
    AppComponent,
    GenderComponent,
    VarianttypesComponent,
    EffecttypesComponent,
    EffecttypesColumnComponent,
    GenotypePreviewTableComponent,
    DatasetsComponent,
    PedigreeSelectorComponent,
    GenotypeBlockComponent,
    GenesBlockComponent,
    RegionsBlockComponent,
    GeneWeightsComponent,
    MinValidatorDirective,
    MaxValidatorDirective,
    GeneSetsComponent,
    SearchableSelectComponent,
    SearchableSelectTemplateDirective,
    BoldMatchingPipe,
    PresentInChildComponent,
    PresentInParentComponent,
    GeneSymbolsComponent,
    RegionsFilterComponent,
    UsersComponent,
    StudyTypesComponent,
    GenotypeBrowserComponent,
    EnrichmentToolComponent,
    EnrichmentModelsComponent,
    EnrichmentTableComponent,
    EnrichmentTableRowComponent,
    FullscreenLoadingComponent,
    EncodeUriComponentPipe,
    EnrichmentModelsBlockComponent,
    PersonFiltersComponent,
    FamilyFiltersBlockComponent,
    ContinuousFilterComponent,
    MultiContinuousFilterComponent,
    CategoricalFilterComponent,
    FamilyIdsComponent,
    NumberWithExpPipe,
    PhenoToolComponent,
    PhenoMeasureSelectorComponent,
    PhenoToolMeasureComponent,
    PhenoToolGenotypeBlockComponent,
    PhenoToolResultsChartComponent,
    PhenoToolResultsChartPerEffectComponent,
    PhenoToolResultsChartPerResultComponent,
    PhenoToolEffectTypesComponent,
    FamilyCountersComponent,
    RegistrationComponent,
    ForgotPasswordComponent,
    PhenoBrowserComponent,
    ResetPasswordComponent,
    PhenoBrowserModalContentComponent,
    PhenoBrowserTableComponent,
    PValueIntensityPipe,
    VariantReportsComponent,
    DatasetDescriptionComponent,
    GenomicScoresComponent,
    GenomicScoresBlockComponent,
    UserInfoPipe,
    UserManagementComponent,
    UsersTableComponent,
    GroupsTableComponent,
    UserEditComponent,
    ManagementComponent,
    UserCreateComponent,
    GroupsBulkAddComponent,
    GroupsBulkRemoveComponent,
    UserGroupsSelectorComponent,
    UsersActionsComponent,
    DatasetsTableComponent,
    GenotypeBrowserSingleViewComponent,
    GenotypePreviewFieldComponent,
    ErrorsAlertComponent,
    ShareQueryButtonComponent,
    LoadQueryComponent,
    PerfectlyDrawablePedigreeComponent,
    NonPdpPedigreesComponent,
    SmallRemoveButtonComponent,
    StudyFiltersBlockComponent,
    StudyFilterComponent,
    AddButtonComponent,
    RemoveButtonComponent,
    PopupComponent,
    PresentInRoleComponent,
    SaveQueryComponent,
    SavedQueriesTableComponent,
    SavedQueriesComponent,
    InheritancetypesComponent,
    GeneBrowserComponent,
    GlobalErrorDisplayComponent,
    GeneViewComponent,
    CommonReportsRowComponent,
    CommonReportsPedigreeCellComponent,
    GeneSymbolsWithSearchComponent,
    LoadingSpinnerComponent,
    DatasetNodeComponent,
    AutismGeneProfilesTableComponent,
    MultipleSelectMenuComponent,
    AutismGeneProfilesBlockComponent,
    AutismGeneProfileSingleViewComponent,
    MiddleClickDirective,
    PersonFiltersBlockComponent,
    PersonIdsComponent,
    FamilyTypeFilterComponent,
    SortingButtonsComponent,
    AutismGeneProfileSingleViewWrapperComponent,
    CheckboxListComponent,
  ],
  imports: [
    BrowserModule,
    FormsModule,
    NgbModule,
    GpfTableModule,
    PedigreeChartModule,
    HistogramModule,
    RouterModule.forRoot(appRoutes, {onSameUrlNavigation: 'reload'}),
    BrowserAnimationsModule,
    MarkdownModule.forRoot(),
    HttpClientModule,
    ConfirmationPopoverModule.forRoot({
      confirmButtonType: 'danger'
    }),
    NgMultiSelectDropDownModule.forRoot(),
    Ng2SearchPipeModule,
    NgxsModule.forRoot([
      VarianttypesState, EffecttypesState, GenderState,
      InheritancetypesState, PersonIdsState, PresentInChildState,
      GeneSymbolsState, FamilyIdsState, RegionsFilterState, StudyTypesState,
    ]),
  ],
  providers: [
    CookieService,
    ConfigService,
    DatasetsService,
    QueryService,
    GeneWeightsService,
    GeneSetsService,
    UsersService,
    EnrichmentModelsService,
    EnrichmentQueryService,
    FullscreenLoadingService,
    StateRestoreService,
    MeasuresService,
    PhenoToolService,
    FamilyCountersService,
    PhenoBrowserService,
    PValueIntensityPipe,
    VariantReportsService,
    GenomicScoresBlockService,
    UsersGroupsService,
    PedigreeMockService,
    PerfectlyDrawablePedigreeService,
    {
      provide: ErrorHandler,
      useClass: GlobalErrorHandler
    },
    {
      provide: RouteReuseStrategy,
      useClass: TaggingRouteReuseStrategy
    },
    BnNgIdleService
  ],

  bootstrap: [AppComponent]
})
export class AppModule { }
