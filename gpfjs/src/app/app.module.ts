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

import { CookieModule } from 'ngx-cookie';

import { GenotypeBrowserComponent } from './genotype-browser/genotype-browser.component';
import { GpfTabsetComponent } from './tabset/tabset.component';

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
import { PhenoFiltersComponent } from './pheno-filters/pheno-filters.component';
import { FamilyFiltersBlockComponent } from './family-filters-block/family-filters-block.component';
import { ContinuousFilterComponent } from './continuous-filter/continuous-filter.component';
import { MultiContinuousFilterComponent } from './multi-continuous-filter/multi-continuous-filter.component';
import { CategoricalFilterComponent } from './categorical-filter/categorical-filter.component';
import { MeasuresService } from './measures/measures.service';
import { FamilyIdsComponent } from './family-ids/family-ids.component';

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

import { NgxMdModule } from 'ngx-md';
import { UserManagementComponent } from './user-management/user-management.component';
import { UserInfoPipe } from './users/user-info.pipe';
import { UsersTableComponent } from './users-table/users-table.component';
import { GroupsTableComponent } from './groups-table/groups-table.component';
import { UserEditComponent } from './user-edit/user-edit.component';
import { ManagementComponent } from './management/management.component';
import { UsersGroupsService } from './users-groups/users-groups.service';

import { Select2Module } from 'ng2-select2';
import { ConfirmationPopoverModule } from 'angular-confirmation-popover';
import { UserCreateComponent } from './user-create/user-create.component';
import { GroupsBulkAddComponent } from './groups-bulk-add/groups-bulk-add.component';
import { GroupsBulkRemoveComponent } from './groups-bulk-remove/groups-bulk-remove.component';
import { UserGroupsSelectorComponent } from './user-groups-selector/user-groups-selector.component';
import { UsersActionsComponent } from './users-actions/users-actions.component';
import { DatasetsTableComponent } from './datasets-table/datasets-table.component';
import { GenotypePreviewChromosomesComponent } from './genotype-preview-chromosomes/genotype-preview-chromosomes.component';
import { ChromosomeService } from './chromosome-service/chromosome.service';
import { ChromosomeComponent } from './chromosome/chromosome.component';
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
import { GlobalErrorHandler } from './global-error-handler/global-error-handler';
import { GlobalErrorDisplayComponent } from './global-error-display/global-error-display.component';
import { DatasetPermissionGuard } from './dataset-permission.guard';

const appRoutes: Routes = [
  {
    path: 'pedigrees',
    component: NonPdpPedigreesComponent
  },
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
        path: 'browser',
        component: GenotypeBrowserSingleViewComponent
      },
      {
        path: 'enrichment',
        component: EnrichmentToolComponent
      },
      {
        path: 'phenoTool',
        component: PhenoToolComponent
      },
      {
        path: 'phenotypeBrowser',
        component: PhenoBrowserComponent
      },
      {
        path: 'description',
        component: DatasetDescriptionComponent
      },
      {
        path: 'commonReport',
        component: VariantReportsComponent,
      }
    ]
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
    path: 'load-query/:uuid',
    component: LoadQueryComponent
  },
  {
    path: 'queries',
    component: SavedQueriesComponent
  },
  {
    path: '**',
    redirectTo: 'datasets'
  },
  {
    path: 'validate/:validateString',
    component: ResetPasswordComponent,
    outlet: 'popup'
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
    GpfTabsetComponent,
    EnrichmentToolComponent,
    EnrichmentModelsComponent,
    EnrichmentTableComponent,
    EnrichmentTableRowComponent,
    FullscreenLoadingComponent,
    EncodeUriComponentPipe,
    EnrichmentModelsBlockComponent,
    PhenoFiltersComponent,
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
    GenotypePreviewChromosomesComponent,
    ChromosomeComponent,
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
    GlobalErrorDisplayComponent,
  ],
  imports: [
    BrowserModule,
    FormsModule,
    NgbModule.forRoot(),
    GpfTableModule,
    PedigreeChartModule,
    HistogramModule,
    RouterModule.forRoot(appRoutes),
    CookieModule.forRoot(),
    BrowserAnimationsModule,
    NgxMdModule.forRoot(),
    Select2Module,
    HttpClientModule,
    ConfirmationPopoverModule.forRoot({
      confirmButtonType: 'danger'
    })
  ],
  providers: [
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
    ChromosomeService,
    PedigreeMockService,
    PerfectlyDrawablePedigreeService,
    {
      provide: ErrorHandler,
      useClass: GlobalErrorHandler
    },
    {
      provide: RouteReuseStrategy,
      useClass: TaggingRouteReuseStrategy
    }
  ],

  entryComponents: [
    RegistrationComponent,
    ForgotPasswordComponent,
    PhenoBrowserModalContentComponent,
    PopupComponent,
    GlobalErrorDisplayComponent
  ],

  bootstrap: [AppComponent]
})
export class AppModule { }
