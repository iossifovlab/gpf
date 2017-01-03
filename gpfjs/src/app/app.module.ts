import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpModule } from '@angular/http';

import { MaterialModule } from '@angular/material';

import { AppComponent } from './app.component';
import 'hammerjs';
import { PhenotypesComponent } from './phenotypes/phenotypes.component';
import { DatasetService, DatasetServiceInterface } from './dataset/dataset.service';

@NgModule({
  declarations: [
    AppComponent,
    PhenotypesComponent
  ],
  imports: [
    BrowserModule,
    FormsModule,
    HttpModule,
    MaterialModule.forRoot()
  ],
  providers: [
    DatasetService
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
