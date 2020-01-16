import { Component, ViewChild } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { ErrorsAlertComponent } from '../errors-alert/errors-alert.component';
import { StateRestoreService } from '../store/state-restore.service';
import { InheritancetypesComponent } from './inheritancetypes.component';


@Component({
  template: `
    <gpf-inheritancetypes #inheritancetypesdom
      [inheritanceTypeFilter]="inheritanceTypesSample"
      [selectedInheritanceTypeFilterValues]="selectedInheritanceTypesSample"
    >
    </gpf-inheritancetypes>`
})
class InheritancetypesHostComponent {
  @ViewChild('inheritancetypesdom')
  public inheritanceTypesComponent: InheritancetypesComponent;

  inheritanceTypesSample: Array<string> = ['mendelian', 'denovo', 'reference', '1234nonexistent'];
  selectedInheritanceTypesSample: Array<string> = ['denovo'];
}


describe('InheritancetypesComponent', () => {
  let hostComponent: InheritancetypesHostComponent;
  let hostFixture: ComponentFixture<InheritancetypesHostComponent>;

  let stateRestoreServiceStub: Partial<StateRestoreService> = {
    getState(stateName: string) {
      return of({'inheritanceTypes': false});
    }
  };

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [
        ErrorsAlertComponent,
        InheritancetypesComponent,
        InheritancetypesHostComponent,
      ],
      providers: [
        { provide: StateRestoreService, useValue: stateRestoreServiceStub }
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    hostFixture = TestBed.createComponent(InheritancetypesHostComponent);
    hostComponent = hostFixture.componentInstance;
    hostFixture.detectChanges();
  });

  it('should create', () => {
    expect(hostComponent).toBeTruthy();
  });

  it('should fill the inheritance type sets correctly', () => {
    let available = hostComponent.inheritanceTypesComponent.inheritanceTypes.available;
    let selected = hostComponent.inheritanceTypesComponent.inheritanceTypes.selected;
    expect(available).toEqual(new Set(['mendelian', 'denovo', 'reference', '1234nonexistent']));
    expect(selected).toEqual(new Set(['denovo']));
  });

  it('should create the appropriate checkboxes with appropriate display names', () => {
      const textSelect = hostFixture.nativeElement.innerText;
      const checkboxes = hostFixture.debugElement.children[0].queryAll((el) => el.nativeElement.type == 'checkbox');
      expect(checkboxes.length).toBe(4);
      expect(textSelect).toEqual(jasmine.stringMatching('Mendelian'));
      expect(textSelect).toEqual(jasmine.stringMatching('Denovo'));
      expect(textSelect).toEqual(jasmine.stringMatching('Reference'));
      expect(textSelect).toEqual(jasmine.stringMatching('1234nonexistent'));
  });

  it('should select the checkboxes for the default selected inheritance types', () => {
      const labels = hostFixture.debugElement.children[0].nativeElement.getElementsByTagName('label');

      let denovoLabel = null;
      for (let label of labels) {
        if (label.innerText.indexOf('Denovo') != -1) {
          denovoLabel = label;
          break;
        }
      }

      expect(denovoLabel).toBeTruthy();
      expect(denovoLabel.children.length).toEqual(1);
      expect(denovoLabel.children[0]).toBeTruthy();
      expect(denovoLabel.children[0].type).toEqual('checkbox');
      expect(denovoLabel.children[0].checked).toBe(true);
  });
});
