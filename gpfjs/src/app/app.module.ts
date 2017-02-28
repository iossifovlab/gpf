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
import { QuerySubmitterComponent } from './query/query-submitter.component';

import { GpfTableModule } from './table/table.module';
import { DatasetsComponent } from './datasets/datasets.component';
import { PedigreeSelectorComponent } from './pedigree-selector/pedigree-selector.component';
import { GenotypeBlockComponent } from './genotype-block/genotype-block.component';
import { GenesBlockComponent } from './genes-block/genes-block.component';
import { GeneSymbolsComponent } from './gene-symbols/gene-symbols.component';
import { RegionsFilterComponent } from './regions-filter/regions-filter.component';
import { RegionsFilterValidatorDirective } from './regions-filter/regions-filter.validator';
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
    QuerySubmitterComponent,
    GeneSetsComponent,
    SearchableSelectComponent,
    SearchableSelectTemplateDirective,
    BoldMatchingPipe,
    PresentInChildComponent,
    PresentInParentComponent,
    GeneSymbolsComponent,
    RegionsFilterComponent,
    RegionsFilterValidatorDirective,
    UsersComponent
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

  ],
  providers: [
    ConfigService,
    DatasetsService,
    QueryService,
    { provide: RequestOptions, useClass: CustomRequestOptions },
    GeneWeightsService,
    GeneSetsService,
    UsersService
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
