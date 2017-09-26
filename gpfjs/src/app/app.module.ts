import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpModule } from '@angular/http';
import { RequestOptions } from '@angular/http';

import { NgbModule } from '@ng-bootstrap/ng-bootstrap';

import { AppComponent } from './app.component';

import { DatasetsService } from './datasets/datasets.service';
import { ConfigService } from './config/config.service';
import { CustomRequestOptions } from './config/customrequest.options';
import { GenderComponent } from './gender/gender.component';
import { PresentInChildComponent } from './present-in-child/present-in-child.component';
import { PresentInParentComponent } from './present-in-parent/present-in-parent.component';
import { VarianttypesComponent } from './varianttypes/varianttypes.component';
import { EffecttypesComponent, EffecttypesColumnComponent } from './effecttypes/effecttypes.component';
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

import { StoreModule } from '@ngrx/store';
import { StoreDevtoolsModule } from '@ngrx/store-devtools';

import { gpfReducer } from './store/gpf-store';
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

import { RouterModule, Routes } from '@angular/router';
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

import { StudiesSummariesComponent } from './studies-summaries/studies-summaries.component';
import { StudiesSummariesService } from './studies-summaries/studies-summaries.service';

import { PValueIntensityPipe } from './utils/p-value-intensity.pipe';

import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { CommonReportsComponent } from './common-reports/common-reports.component';
import { VariantReportsComponent } from './variant-reports/variant-reports.component';
import { VariantReportsService } from './variant-reports/variant-reports.service';
import { DatasetDescriptionComponent } from './dataset-description/dataset-description.component';

import { MarkdownModule } from 'angular2-markdown';
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

const appRoutes: Routes = [
  {
    path: 'datasets',
    component: DatasetsComponent
  },
  {
    path: 'datasets/:dataset',
    component: DatasetsComponent,
    children: [
      {
        path: 'browser',
        component: GenotypeBrowserComponent
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
        path: '**',
        redirectTo: 'browser'
      }
    ]
  },
  {
    path: 'reports',
    component: CommonReportsComponent,
    children: [
      {
        path: '',
        pathMatch: 'full',
        redirectTo: 'summary',
      },
      {
        path: 'summary',
        component: StudiesSummariesComponent
      },
      {
        path: 'reports',
        component: VariantReportsComponent
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
    StudiesSummariesComponent,
    CommonReportsComponent,
    VariantReportsComponent,
    DatasetDescriptionComponent,
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
  ],
  imports: [
    BrowserModule,
    FormsModule,
    HttpModule,
    NgbModule.forRoot(),
    GpfTableModule,
    PedigreeChartModule,
    HistogramModule,
    StoreModule.provideStore(gpfReducer),
    StoreDevtoolsModule.instrumentOnlyWithExtension(),
    RouterModule.forRoot(appRoutes),
    CookieModule.forRoot(),
    BrowserAnimationsModule,
    MarkdownModule.forRoot(),
    Select2Module,
    ConfirmationPopoverModule.forRoot({
      confirmButtonType: 'danger'
    })
  ],
  providers: [
    ConfigService,
    DatasetsService,
    QueryService,
    { provide: RequestOptions, useClass: CustomRequestOptions },
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
    StudiesSummariesService,
    VariantReportsService,
    UsersGroupsService,
  ],

  entryComponents: [
    RegistrationComponent,
    ForgotPasswordComponent,
    PhenoBrowserModalContentComponent
  ],

  bootstrap: [AppComponent]
})
export class AppModule { }
