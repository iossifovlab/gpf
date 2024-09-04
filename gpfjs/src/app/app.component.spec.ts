import { TestBed } from '@angular/core/testing';
import { AppComponent } from './app.component';
import { GenderComponent } from './gender/gender.component';
import { VariantTypesComponent } from './variant-types/variant-types.component';
import { DatasetsService } from './datasets/datasets.service';
import { DatasetsComponent } from './datasets/datasets.component';
import { EffectTypesComponent } from './effect-types/effect-types.component';
import { GenotypeBlockComponent } from './genotype-block/genotype-block.component';
import { RegionsBlockComponent } from './regions-block/regions-block.component';
import { GenesBlockComponent } from './genes-block/genes-block.component';
import { PedigreeSelectorComponent } from './pedigree-selector/pedigree-selector.component';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { EffecttypesColumnComponent } from './effect-types/effect-types-column.component';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ConfigService } from './config/config.service';
import { UsersService } from './users/users.service';
import { RouterTestingModule } from '@angular/router/testing';
import { FullscreenLoadingComponent } from './fullscreen-loading/fullscreen-loading.component';
import { UsersComponent } from './users/users.component';
import { FullscreenLoadingService } from './fullscreen-loading/fullscreen-loading.service';
import { FormsModule } from '@angular/forms';
import { APP_BASE_HREF } from '@angular/common';
import { UserInfoPipe } from './users/user-info.pipe';
import { StoreModule } from '@ngrx/store';
import { datasetIdReducer } from './datasets/datasets.state';


class MockDatasetsService {
  public getSelectedDataset(): object {
    return { id: 'testDataset' };
  }
}

describe('AppComponent', () => {
  const datasetsServiceMock = new MockDatasetsService();

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [
        AppComponent,
        DatasetsComponent,
        GenderComponent,
        VariantTypesComponent,
        EffectTypesComponent,
        EffecttypesColumnComponent,
        GenotypeBlockComponent,
        RegionsBlockComponent,
        GenesBlockComponent,
        PedigreeSelectorComponent,
        FullscreenLoadingComponent,
        UsersComponent,
        UserInfoPipe
      ],
      imports: [
        NgbModule,
        HttpClientTestingModule,
        RouterTestingModule,
        FormsModule,
        StoreModule.forRoot({datasetId: datasetIdReducer})
      ],
      providers: [
        { provide: DatasetsService, useValue: datasetsServiceMock },
        ConfigService,
        UsersService,
        FullscreenLoadingService,
        { provide: APP_BASE_HREF, useValue: '' }
      ]
    });
    TestBed.compileComponents();
  });

  it('should create the app', () => {
    const fixture = TestBed.createComponent(AppComponent);
    const app = fixture.debugElement.componentInstance;
    expect(app).toBeTruthy();
  });

  it('should have as title "GPF: Genotypes and Phenotypes in Families"', () => {
    const fixture = TestBed.createComponent(AppComponent);
    const app = fixture.debugElement.componentInstance;
    expect(app.title).toStrictEqual(app.title);
  });

  it('should render title in a h3 tag', () => {
    const fixture = TestBed.createComponent(AppComponent);
    fixture.detectChanges();
    const compiled = fixture.debugElement.nativeElement;
    const app = fixture.debugElement.componentInstance;
    expect(compiled.querySelector('h3').textContent).toContain(app.title);
  });
});
