import { Component, EventEmitter, HostListener, Input, OnChanges, OnInit, Output, ViewChildren } from '@angular/core';
import { Observable, ReplaySubject } from 'rxjs';
import { AutismGeneToolConfig, AutismGeneToolGene } from './autism-gene-profile';
import { AutismGeneProfilesService } from './autism-gene-profiles.service';
import { NgbDropdownMenu } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'gpf-autism-gene-profiles',
  templateUrl: './autism-gene-profiles.component.html',
  styleUrls: ['./autism-gene-profiles.component.css']
})
export class AutismGeneProfilesComponent implements OnInit, OnChanges {
  @Input() config: AutismGeneToolConfig;
  @Output() createTabEvent = new EventEmitter();
  @ViewChildren(NgbDropdownMenu) ngbDropdownMenu: NgbDropdownMenu[];

  private genes: AutismGeneToolGene[] = [];
  private shownGeneLists: string[];
  private shownAutismScores: string[];
  private shownProtectionScores: string[];

  private pageIndex = 1;
  private loadMoreGenes = true;
  private scrollLoadThreshold = 1000;

  geneInput = '';

  @HostListener('window:scroll', ['$event'])
  onWindowScroll(event: any) {
    const currentScrollHeight = document.documentElement.scrollTop + document.documentElement.offsetHeight;
    const totalScrollHeight = document.documentElement.scrollHeight;

    if (this.loadMoreGenes && currentScrollHeight + this.scrollLoadThreshold >= totalScrollHeight) {
      this.updateGenes();
    }
  }

  constructor(
    private autismGeneProfilesService: AutismGeneProfilesService,
  ) { }

  ngOnChanges(): void {
    if (this.config) {
      this.shownGeneLists = this.config['geneLists'];
      this.shownAutismScores = this.config['autismScores'];
      this.shownProtectionScores = this.config['protectionScores'];
    }
  }

  ngOnInit(): void {
    this.autismGeneProfilesService.getGenes(this.pageIndex).take(1).subscribe(res => {
      this.genes = this.genes.concat(res);
    });
  }

  calculateDatasetColspan(datasetConfig) {
    return datasetConfig.effects.length * datasetConfig.personSets.length;
  }

  handleMultipleSelectMenuApplyEvent($event) {
    if ($event.id === 'geneLists') {
      this.shownGeneLists = $event.data;
    } else if ($event.id === 'autismScores') {
      this.shownAutismScores = $event.data;
    } else if ($event.id === 'protectionScores') {
      this.shownProtectionScores = $event.data;
    }

    this.ngbDropdownMenu.forEach(menu => menu.dropdown.close());
  }

  emitCreateTabEvent(geneSymbol: string, openTab: boolean): void {
    this.createTabEvent.emit({geneSymbol: geneSymbol, openTab: openTab});
  }

  updateGenes() {
    this.loadMoreGenes = false;
    this.pageIndex++;

    this.autismGeneProfilesService.getGenes(this.pageIndex, this.geneInput).take(1).subscribe(res => {
      this.genes = this.genes.concat(res);
      this.loadMoreGenes = Object.keys(res).length !== 0 ? true : false;
    });
  }

  search(value: string) {
    this.geneInput = value;
    this.genes = [];
    this.pageIndex = 0;

    this.updateGenes();
  }
}
