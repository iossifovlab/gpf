/* eslint-disable no-unused-vars, @typescript-eslint/no-unused-vars */
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { NgxsModule } from '@ngxs/store';
import { of } from 'rxjs';

import { GeneSymbolsComponent } from 'app/gene-symbols/gene-symbols.component';
import { GenesBlockComponent } from './genes-block.component';
import { GeneSymbolsState } from 'app/gene-symbols/gene-symbols.state';
import { FormsModule } from '@angular/forms';

describe('GenesBlockComponent', () => {
  let component: GenesBlockComponent;
  let fixture: ComponentFixture<GenesBlockComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [GeneSymbolsComponent, GenesBlockComponent],
      imports: [NgbModule, NgxsModule.forRoot([GeneSymbolsState], {developmentMode: true}), FormsModule],
    }).compileComponents();
    fixture = TestBed.createComponent(GenesBlockComponent);
    component = fixture.componentInstance;
    component['store'] = {
      selectOnce: () => of({geneSymbols: ['value1', 'value2']}),
      dispatch: () => ({})
    } as never;
    fixture.detectChanges();
  }));
  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
