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
import { StudytypesComponent } from './studytypes/studytypes.component';
import { EffecttypesComponent } from './effecttypes/effecttypes.component';
import { GenotypePreviewTableComponent } from './genotype-preview-table/genotype-preview-table.component';
import { QueryService } from './query/query.service';

@NgModule({
  declarations: [
    AppComponent,
    PhenotypesComponent,
    GenderComponent,
    VarianttypesComponent,
    StudytypesComponent,
    EffecttypesComponent,
    GenotypePreviewTableComponent
  ],
  imports: [
    BrowserModule,
    FormsModule,
    HttpModule,
    NgbModule
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

