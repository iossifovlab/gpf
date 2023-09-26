/* eslint-disable max-len */
import { BrowserModule } from '@angular/platform-browser';
import { NgModule, ErrorHandler, APP_INITIALIZER } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { AppComponent } from './app.component';
import { DatasetsService } from './datasets/datasets.service';
import { ConfigService } from './config/config.service';
import { GenderComponent } from './gender/gender.component';
import { PresentInChildComponent } from './present-in-child/present-in-child.component';
import { PresentInChildState } from './present-in-child/present-in-child.state';
import { PresentInParentComponent } from './present-in-parent/present-in-parent.component';
import { PresentInParentState } from './present-in-parent/present-in-parent.state';
import { VariantTypesComponent } from './variant-types/variant-types.component';
import { EffectTypesComponent } from './effect-types/effect-types.component';
import { EffecttypesColumnComponent } from './effect-types/effect-types-column.component';
import { GenotypePreviewTableComponent } from './genotype-preview-table/genotype-preview-table.component';
import { QueryService } from './query/query.service';
import { GpfTableModule } from './table/table.module';
import { DatasetsComponent } from './datasets/datasets.component';
import { PedigreeSelectorComponent } from './pedigree-selector/pedigree-selector.component';
import { PedigreeSelectorState } from './pedigree-selector/pedigree-selector.state';
import { GenotypeBlockComponent } from './genotype-block/genotype-block.component';
import { GenesBlockComponent } from './genes-block/genes-block.component';
import { GeneSymbolsComponent } from './gene-symbols/gene-symbols.component';
import { GeneSymbolsState } from './gene-symbols/gene-symbols.state';
import { RegionsFilterComponent } from './regions-filter/regions-filter.component';
import { RegionsBlockComponent } from './regions-block/regions-block.component';
import { HistogramModule } from './histogram/histogram.module';
import { GeneScoresComponent } from './gene-scores/gene-scores.component';
import { GeneScoresService } from './gene-scores/gene-scores.service';
import { GeneScoresState } from './gene-scores/gene-scores.state';
import { GeneSetsComponent } from './gene-sets/gene-sets.component';
import { GeneSetsState } from './gene-sets/gene-sets.state';
import { GeneSetsService } from './gene-sets/gene-sets.service';
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
import { EnrichmentModelsState } from './enrichment-models/enrichment-models.state';
import { EnrichmentQueryService } from './enrichment-query/enrichment-query.service';
import { EnrichmentTableComponent } from './enrichment-table/enrichment-table.component';
import { EnrichmentTableRowComponent } from './enrichment-table/enrichment-table-row.component';
import { FullscreenLoadingComponent } from './fullscreen-loading/fullscreen-loading.component';
import { FullscreenLoadingService } from './fullscreen-loading/fullscreen-loading.service';
import { EncodeUriComponentPipe } from './utils/encode-uri-component.pipe';
import { Router, RouterModule, Routes, UrlSerializer } from '@angular/router';
import { PersonFiltersComponent } from './person-filters/person-filters.component';
import { PersonFiltersState } from './person-filters/person-filters.state';
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
import { PhenoToolMeasureState } from './pheno-tool-measure/pheno-tool-measure.state';
import { PhenoToolGenotypeBlockComponent } from './pheno-tool-genotype-block/pheno-tool-genotype-block.component';
import { PhenoToolService } from './pheno-tool/pheno-tool.service';
import { PhenoToolResultsChartComponent } from './pheno-tool-results-chart/pheno-tool-results-chart.component';
import { PhenoToolResultsChartPerEffectComponent } from './pheno-tool-results-chart/pheno-tool-results-chart-per-effect.component';
import { PhenoToolResultsChartPerResultComponent } from './pheno-tool-results-chart/pheno-tool-results-chart-per-result.component';
import { PhenoToolEffectTypesComponent } from './pheno-tool-effect-types/pheno-tool-effect-types.component';
import { PhenoBrowserComponent } from './pheno-browser/pheno-browser.component';
import { PhenoBrowserService } from './pheno-browser/pheno-browser.service';
import { PhenoBrowserModalContentComponent } from './pheno-browser-modal-content/pheno-browser-modal-content.component';
import { PhenoBrowserTableComponent } from './pheno-browser-table/pheno-browser-table.component';
import { PValueIntensityPipe } from './utils/p-value-intensity.pipe';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { PeopleCounterRowPipe, VariantReportsComponent } from './variant-reports/variant-reports.component';
import { VariantReportsService } from './variant-reports/variant-reports.service';
import { DatasetDescriptionComponent } from './dataset-description/dataset-description.component';
import { GenomicScoresComponent } from './genomic-scores/genomic-scores.component';
import { GenomicScoresBlockComponent } from './genomic-scores-block/genomic-scores-block.component';
import { GenomicScoresBlockState } from './genomic-scores-block/genomic-scores-block.state';
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
import { UserGroupsSelectorComponent } from './user-groups-selector/user-groups-selector.component';
import { DatasetsTableComponent } from './datasets-table/datasets-table.component';
import { GenotypeBrowserSingleViewComponent } from './genotype-browser-single-view/genotype-browser-single-view.component';
import { GenotypePreviewFieldComponent } from './genotype-preview-field/genotype-preview-field.component';
import { ErrorsAlertComponent } from './errors-alert/errors-alert.component';
import { LoadQueryComponent } from './load-query/load-query.component';
import { PerfectlyDrawablePedigreeComponent } from './perfectly-drawable-pedigree/perfectly-drawable-pedigree.component';
import { PedigreeMockService } from './perfectly-drawable-pedigree/pedigree-mock.service';
import { NonPdpPedigreesComponent } from './non-pdp-pedigrees/non-pdp-pedigrees.component';
import { PerfectlyDrawablePedigreeService } from './perfectly-drawable-pedigree/perfectly-drawable-pedigree.service';
import { StudyFiltersComponent } from './study-filters/study-filters.component';
import { StudyFiltersState } from './study-filters/study-filters.state';
import { AddButtonComponent } from './add-button/add-button.component';
import { RemoveButtonComponent } from './remove-button/remove-button.component';
import { PopupComponent } from './popup/popup.component';
import { SaveQueryComponent } from './save-query/save-query.component';
import { SavedQueriesTableComponent } from './saved-queries-table/saved-queries-table.component';
import { UserProfileComponent } from './user-profile/user-profile.component';
import { InheritancetypesComponent } from './inheritancetypes/inheritancetypes.component';
import { InheritancetypesState } from './inheritancetypes/inheritancetypes.state';
import { GeneBrowserComponent } from './gene-browser/gene-browser.component';
import { GlobalErrorHandler } from './global-error-handler/global-error-handler';
import { GlobalErrorDisplayComponent } from './global-error-display/global-error-display.component';
import { NgMultiSelectDropDownModule } from 'ng-multiselect-dropdown';
import { CommonReportsRowComponent } from './variant-reports/common-reports-row/common-reports-row.component';
import { CommonReportsPedigreeCellComponent } from './variant-reports/common-reports-pedigree-cell/common-reports-pedigree-cell.component';
import { LoadingSpinnerComponent } from './loading-spinner/loading-spinner.component';
import { DatasetNodeComponent } from './dataset-node/dataset-node.component';
import { MultipleSelectMenuComponent } from './multiple-select-menu/multiple-select-menu.component';
import { AutismGeneProfilesBlockComponent } from './autism-gene-profiles-block/autism-gene-profiles-block.component';
import { AutismGeneProfileSingleViewComponent } from './autism-gene-profiles-single-view/autism-gene-profile-single-view.component';
import { PersonFiltersBlockComponent } from './person-filters-block/person-filters-block.component';
import { PersonIdsComponent } from './person-ids/person-ids.component';
import { PersonIdsState } from './person-ids/person-ids.state';
import { FamilyTypeFilterComponent } from './family-type-filter/family-type-filter.component';
import { FamilyTypeFilterState } from './family-type-filter/family-type-filter.state';
import { SortingButtonsComponent } from './sorting-buttons/sorting-buttons.component';
import { BnNgIdleService } from 'bn-ng-idle';
import { NgxsModule } from '@ngxs/store';
import { NgxsResetPluginModule } from 'ngxs-reset-plugin';
import { VarianttypesState } from './variant-types/variant-types.state';
import { EffecttypesState } from './effect-types/effect-types.state';
import { GenderState } from './gender/gender.state';
import { RegionsFilterState } from './regions-filter/regions-filter.state';
import { CheckboxListComponent, DisplayNamePipe } from './checkbox-list/checkbox-list.component';
import { ErrorsState } from './common/errors.state';
import { toolPageLinks } from './datasets/datasets';
import { GenePlotComponent } from './gene-plot/gene-plot.component';
import { DragDropModule } from '@angular/cdk/drag-drop';
import { ClipboardModule } from '@angular/cdk/clipboard';
import { SplitPipe } from './utils/split.pipe';
import { MiddleClickDirective } from './autism-gene-profiles-table/middle-click.directive';
import { AgpTableComponent } from './autism-gene-profiles-table/autism-gene-profiles-table.component';
import { AutismGeneProfileSingleViewWrapperComponent } from './autism-gene-profiles-single-view-wrapper/autism-gene-profiles-single-view-wrapper.component';
import { TruncatePipe } from './utils/truncate.pipe';
import { UniqueFamilyVariantsFilterComponent } from './unique-family-variants-filter/unique-family-variants-filter.component';
import { UniqueFamilyVariantsFilterState } from './unique-family-variants-filter/unique-family-variants-filter.state';
import { AngularMarkdownEditorModule } from 'angular-markdown-editor';
import { PedigreeChartComponent } from './pedigree-chart/pedigree-chart.component';
import { PedigreeChartMemberComponent } from './pedigree-chart/pedigree-chart-member.component';
import { JoinPipe } from './utils/join.pipe';
import { LegendComponent } from './legend/legend.component';
import { PedigreeComponent } from './pedigree/pedigree.component';
import { AuthInterceptorService } from './auth-interceptor.service';
import { AuthResolverService } from './auth-resolver.service';
import { APP_BASE_HREF, PlatformLocation } from '@angular/common';
import { CustomUrlSerializer } from './custom-url-serializer';
import { ComparePipe } from './utils/compare.pipe';
import { BackgroundColorPipe } from './utils/background-color.pipe';
import { RegressionComparePipe } from './utils/regression-compare.pipe';
import { GetRegressionIdsPipe } from './utils/get-regression-ids.pipe';
import { GetEffectTypeOrderByColumOrderPipe } from './utils/get-effect-type-order-by-column-order.pipe';
import { GetVariantReportRowsPipe } from './utils/get-variant-report-rows.pipe';
import { BackgroundColorEnrichmentPipe } from './utils/background-color-enrichment.pipe';
import { ContrastAdjustPipe } from './utils/contrast-adjust.pipe';
import { ItemAddMenuComponent } from './item-add-menu/item-add-menu.component';
import { ConfirmButtonComponent } from './confirm-button/confirm-button.component';
import * as Sentry from '@sentry/angular-ivy';
import * as $ from 'jquery'; // This is a global import, do not remove (even if linter says unused)
import 'jquery-ui/ui/widgets/autocomplete.js'; // This as well
import { FederationCredentialsComponent } from './federation-credentials/federation-credentials.component';
import { StudyFiltersTreeComponent } from './treelist-checkbox/treelist-checkbox.component';
import { LoginComponent } from './login/login.component';
import { DatasetsTreeService } from './datasets/datasets-tree.service';
import { SearchableSelectComponent } from './searchable-select/searchable-select.component';
import { SearchableSelectTemplateDirective } from './searchable-select/searchable-select-template.directive';

const appRoutes: Routes = [
  {
    path: 'login',
    component: LoginComponent,
    resolve: { _: AuthResolverService},
  },
  {
    path: 'datasets',
    component: DatasetsComponent,
  },
  {
    path: 'datasets/:dataset',
    component: DatasetsComponent,
    children: [
      {
        path: toolPageLinks.genotypeBrowser,
        component: GenotypeBrowserSingleViewComponent
      },
      {
        path: toolPageLinks.enrichmentTool,
        component: EnrichmentToolComponent
      },
      {
        path: toolPageLinks.phenotypeTool,
        component: PhenoToolComponent
      },
      {
        path: toolPageLinks.phenotypeBrowser,
        component: PhenoBrowserComponent
      },
      {
        path: toolPageLinks.datasetDescription,
        component: DatasetDescriptionComponent
      },
      {
        path: toolPageLinks.datasetStatistics,
        component: VariantReportsComponent
      },
      {
        path: toolPageLinks.geneBrowser,
        component: GeneBrowserComponent
      },
      {
        path: toolPageLinks.geneBrowser + '/:gene',
        component: GeneBrowserComponent
      }
    ]
  },
  {
    path: 'autism-gene-profiles',
    component: AutismGeneProfilesBlockComponent
  },
  {
    path: 'autism-gene-profiles/:genes',
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
        path: 'users/:id',
        component: UserEditComponent
      }
    ]
  },
  {
    path: 'load-query/:uuid',
    component: LoadQueryComponent
  },
  {
    path: 'user-profile',
    component: UserProfileComponent
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
    VariantTypesComponent,
    EffectTypesComponent,
    EffecttypesColumnComponent,
    GenotypePreviewTableComponent,
    DatasetsComponent,
    PedigreeSelectorComponent,
    GenotypeBlockComponent,
    GenesBlockComponent,
    RegionsBlockComponent,
    GeneScoresComponent,
    MinValidatorDirective,
    MaxValidatorDirective,
    GeneSetsComponent,
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
    PhenoBrowserComponent,
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
    UserGroupsSelectorComponent,
    DatasetsTableComponent,
    GenotypeBrowserSingleViewComponent,
    GenotypePreviewFieldComponent,
    ErrorsAlertComponent,
    LoadQueryComponent,
    PerfectlyDrawablePedigreeComponent,
    NonPdpPedigreesComponent,
    ConfirmButtonComponent,
    StudyFiltersComponent,
    AddButtonComponent,
    RemoveButtonComponent,
    PopupComponent,
    SaveQueryComponent,
    SavedQueriesTableComponent,
    UserProfileComponent,
    InheritancetypesComponent,
    GeneBrowserComponent,
    GlobalErrorDisplayComponent,
    CommonReportsRowComponent,
    CommonReportsPedigreeCellComponent,
    LoadingSpinnerComponent,
    DatasetNodeComponent,
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
    DisplayNamePipe,
    GenePlotComponent,
    PeopleCounterRowPipe,
    SplitPipe,
    ContrastAdjustPipe,
    AgpTableComponent,
    TruncatePipe,
    ComparePipe,
    BackgroundColorPipe,
    BackgroundColorEnrichmentPipe,
    RegressionComparePipe,
    GetRegressionIdsPipe,
    JoinPipe,
    GetEffectTypeOrderByColumOrderPipe,
    GetVariantReportRowsPipe,
    UniqueFamilyVariantsFilterComponent,
    PedigreeChartComponent,
    PedigreeChartMemberComponent,
    LegendComponent,
    PedigreeComponent,
    ItemAddMenuComponent,
    FederationCredentialsComponent,
    StudyFiltersTreeComponent,
    LoginComponent,
    SearchableSelectComponent,
    SearchableSelectTemplateDirective,
  ],
  imports: [
    BrowserModule,
    FormsModule,
    NgbModule,
    GpfTableModule,
    HistogramModule,
    RouterModule.forRoot(appRoutes),
    BrowserAnimationsModule,
    MarkdownModule.forRoot(),
    HttpClientModule,
    ConfirmationPopoverModule.forRoot({
      confirmButtonType: 'danger'
    }),
    NgMultiSelectDropDownModule.forRoot(),
    NgxsModule.forRoot([
      VarianttypesState, EffecttypesState, GenderState,
      InheritancetypesState, PersonIdsState, PresentInChildState, PresentInParentState,
      GeneSymbolsState, FamilyIdsState, RegionsFilterState, StudyTypesState, GeneSetsState,
      GeneScoresState, EnrichmentModelsState, PedigreeSelectorState, FamilyTypeFilterState,
      StudyFiltersState, PersonFiltersState, GenomicScoresBlockState, PhenoToolMeasureState,
      UniqueFamilyVariantsFilterState, ErrorsState
    ], {compatibility: { strictContentSecurityPolicy: true }}
    ),
    NgxsResetPluginModule.forRoot(),
    DragDropModule,
    ClipboardModule,
    AngularMarkdownEditorModule.forRoot()
  ],
  providers: [
    CookieService,
    ConfigService,
    DatasetsService,
    DatasetsTreeService,
    QueryService,
    GeneScoresService,
    GeneSetsService,
    UsersService,
    EnrichmentModelsService,
    EnrichmentQueryService,
    FullscreenLoadingService,
    MeasuresService,
    PhenoToolService,
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
    BnNgIdleService,
    { provide: HTTP_INTERCEPTORS, useClass: AuthInterceptorService, multi: true },
    {
      provide: APP_BASE_HREF,
      useFactory: (s: PlatformLocation) => s.getBaseHrefFromDOM(),
      deps: [PlatformLocation]
    },
    {
      provide: UrlSerializer,
      useClass: CustomUrlSerializer
    },
    {
      provide: ErrorHandler,
      useValue: Sentry.createErrorHandler({
        showDialog: false,
      }),
    },
    {
      provide: Sentry.TraceService,
      deps: [Router],
    },
    {
      provide: APP_INITIALIZER,
      useFactory: () => () => {},
      deps: [Sentry.TraceService],
      multi: true,
    },
  ],

  bootstrap: [AppComponent]
})
export class AppModule { }
