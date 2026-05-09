import { Input, Component, HostListener, OnInit } from '@angular/core';
import { GenotypePreviewVariantsArray } from '../genotype-preview-model/genotype-preview';
import { PersonSet } from '../datasets/datasets';
import { LegendItem } from 'app/variant-reports/variant-reports';

@Component({
  selector: 'gpf-genotype-preview-table',
  templateUrl: './genotype-preview-table.component.html',
  styleUrls: ['./genotype-preview-table.component.css'],
  standalone: false
})
export class GenotypePreviewTableComponent implements OnInit {
  @Input() public genotypePreviewVariantsArray: GenotypePreviewVariantsArray;
  @Input() public columns: Array<any>;
  @Input() public legend: Array<PersonSet> = [];
  public singleColumnWidth: string;
  public legendItems: Array<LegendItem> = [];

  @HostListener('window:resize', ['$event'])
  public onResize(): void {
    const screenWidth = window.innerWidth;
    const columnsCount = this.columns.length;
    const padding = 60;
    const scrollSize = 15;

    this.singleColumnWidth = `${(screenWidth - padding - scrollSize) / columnsCount}px`;
  }

  public ngOnInit(): void {
    if (this.legend) {
      this.legendItems = this.legend.map(item => new LegendItem(item.id, item.name, item.color));
      this.onResize();
    }
  }
}
