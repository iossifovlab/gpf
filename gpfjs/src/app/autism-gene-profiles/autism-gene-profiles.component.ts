import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'gpf-autism-gene-profiles',
  templateUrl: './autism-gene-profiles.component.html',
  styleUrls: ['./autism-gene-profiles.component.css']
})
export class AutismGeneProfilesComponent implements OnInit {
  tableHeaders: string[] = [];
  geneLists: string[];
  autismScores: string[];
  protectionScores: string[];
  affectedStatuses: string[];
  effectTypes: string[];

  genes: string[];

  ngOnInit(): void {
    this.tableHeaders = ["Gene", "Gene lists", "Autism score", "Protection score", "SSC", "SPARK"];
    this.geneLists = ["gene list 1", "gene list 2", "gene list 3", "gene list 4"];
    this.autismScores = ["autism score 1", "autism score 2", "autism score 3", "autism score 4"];
    this.protectionScores = ["protection score 1", "protection score 2", "protection score 3", "protection score 4"];
    this.affectedStatuses = ["affected", "unaffected"];
    this.effectTypes = ["LGD", "MS", "SYN"];
    this.genes = ["GENE1", "GENE2", "GENE3", "GENE4"];
  }
}
