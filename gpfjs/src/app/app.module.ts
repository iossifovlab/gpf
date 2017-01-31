import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpModule } from '@angular/http';
import { RequestOptions } from '@angular/http';

import { NgbModule } from '@ng-bootstrap/ng-bootstrap';

import { AppComponent } from './app.component';

import { PhenotypesComponent } from './phenotypes/phenotypes.component';
import { DatasetService } from './dataset/dataset.service';
import { ConfigService } from './config/config.service';
import {CustomRequestOptions } from './config/customrequest.options';
import { GenderComponent } from './gender/gender.component';
import { VarianttypesComponent } from './varianttypes/varianttypes.component';
import { EffecttypesComponent } from './effecttypes/effecttypes.component';
import { GenotypePreviewTableComponent } from './genotype-preview-table/genotype-preview-table.component';
import { QueryService } from './query/query.service';

import { GpfTableModule } from './table/table.module';
import { DatasetComponent } from './dataset/dataset.component';
import { PedigreeSelectorComponent } from './pedigree-selector/pedigree-selector.component';
import { GenotypeBlockComponent } from './genotype-block/genotype-block.component';
import { GenesBlockComponent } from './genes-block/genes-block.component';
import { RegionsBlockComponent } from './regions-block/regions-block.component';

@NgModule({
  declarations: [
    AppComponent,
    PhenotypesComponent,
    GenderComponent,
    VarianttypesComponent,
    EffecttypesComponent,
    GenotypePreviewTableComponent,
    DatasetComponent,
    PedigreeSelectorComponent,
    GenotypeBlockComponent,
    GenesBlockComponent,
    RegionsBlockComponent,
  ],
  imports: [
    BrowserModule,
    FormsModule,
    HttpModule,
    NgbModule.forRoot(),
    GpfTableModule
  ],
  providers: [
    ConfigService,
    DatasetService,
    QueryService,
    { provide: RequestOptions, useClass: CustomRequestOptions }
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }

