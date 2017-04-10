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

import { GenotypeBrowserComponent } from './genotype-browser/genotype-browser.component'
import { GpfTabsetComponent } from './tabset/tabset.component'

import { EnrichmentToolComponent } from './enrichment-tool/enrichment-tool.component'
import { EnrichmentModelsBlockComponent } from './enrichment-models-block/enrichment-models-block.component'
import { EnrichmentModelsComponent } from './enrichment-models/enrichment-models.component'
import { EnrichmentModelsService } from './enrichment-models/enrichment-models.service'
import { EnrichmentQueryService } from './enrichment-query/enrichment-query.service';
import { EnrichmentTableComponent } from './enrichment-table/enrichment-table.component'
import { EnrichmentTableRowComponent } from './enrichment-table/enrichment-table-row.component'

import { FullscreenLoadingComponent } from './fullscreen-loading/fullscreen-loading.component'
import { FullscreenLoadingService } from './fullscreen-loading/fullscreen-loading.service'

import { EncodeUriComponentPipe } from './utils/encode-uri-component.pipe';

import { RouterModule, Routes } from '@angular/router';
import { StateRestoreService } from './store/state-restore.service';
import { PhenoFiltersComponent } from './pheno-filters/pheno-filters.component';
import { FamilyFiltersBlockComponent } from './family-filters-block/family-filters-block.component';
import { ContinuousFilterComponent } from './continuous-filter/continuous-filter.component';
import { MultiContinuousFilterComponent } from './multi-continuous-filter/multi-continuous-filter.component';
import { CategoricalFilterComponent } from './categorical-filter/categorical-filter.component'
import { MeasuresService } from './measures/measures.service';
import { FamilyIdsComponent } from './family-ids/family-ids.component'

import { NumberWithExpPipe } from './utils/number-with-exp.pipe';

const appRoutes: Routes = [
  {
    path: '',
    redirectTo: 'datasets',
    pathMatch: 'full'
  },
  {
    path: 'datasets',
    component: DatasetsComponent
  },
  {
    path: 'datasets/:dataset',
    component: DatasetsComponent,
    children: [
      {
        path: '',
        redirectTo: 'browser',
        pathMatch: 'full'
      },
      {
        path: 'browser',
        component: GenotypeBrowserComponent
      },
      {
        path: 'enrichment',
        component: EnrichmentToolComponent
      },
    ]
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
    NumberWithExpPipe
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
    CookieModule.forRoot()

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
    MeasuresService
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
