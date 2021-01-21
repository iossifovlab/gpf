import { Component, OnInit } from '@angular/core';
import { AutismGeneProfilesService } from './autism-gene-profiles.service';

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
  geneRows: {};

  constructor(
    private autismGeneProfilesService: AutismGeneProfilesService,
  ) {
    

    this.tableHeaders = ["Gene", "Gene lists", "Autism score", "Protection score", "SSC", "SPARK"];
    this.geneLists = ["gene list 1", "gene list 2", "gene list 3", "gene list 4"];
    this.autismScores = ["autism score 1", "autism score 2", "autism score 3", "autism score 4"];
    this.protectionScores = ["protection score 1", "protection score 2", "protection score 3", "protection score 4"];
    this.affectedStatuses = ["affected", "unaffected"];
    this.effectTypes = ["LGD", "MS", "SYN"];
  }

  ngOnInit(): void {
    this.geneRows = [
      {
        name: "GENE1",
        geneLists: new Map([["gene list 1", true], ["gene list 2", false], ["gene list 3", true], ["gene list 4", true]]),
        autismScores: new Map([["autism score 1", 1], ["autism score 2", 2], ["autism score 3", 3], ["autism score 4", 4]]),
        protectionScores: new Map([["protection score 1", 5], ["protection score 2", 6], ["protection score 3", 7], ["protection score 4", 8]]),
        datasets: [1,2,3,4,5,6,7,8,9,10,11,12],
      },
      {
        name: "GENE2",
        geneLists: new Map([["gene list 1", true], ["gene list 2", false], ["gene list 3", true], ["gene list 4", true]]),
        autismScores: new Map([["autism score 1", 1], ["autism score 2", 2], ["autism score 3", 3], ["autism score 4", 4]]),
        protectionScores: new Map([["protection score 1", 5], ["protection score 2", 6], ["protection score 3", 7], ["protection score 4", 8]]),
        datasets: [1,2,3,4,5,6,7,8,9,10,11,12],
      },
      {
        name: "GENE3",
        geneLists: new Map([["gene list 1", true], ["gene list 2", false], ["gene list 3", true], ["gene list 4", true]]),
        autismScores: new Map([["autism score 1", 1], ["autism score 2", 2], ["autism score 3", 3], ["autism score 4", 4]]),
        protectionScores: new Map([["protection score 1", 5], ["protection score 2", 6], ["protection score 3", 7], ["protection score 4", 8]]),
        datasets: [1,2,3,4,5,6,7,8,9,10,11,12],
      },
      {
        name: "GENE4",
        geneLists: new Map([["gene list 1", true], ["gene list 2", false], ["gene list 3", true], ["gene list 4", true]]),
        autismScores: new Map([["autism score 1", 1], ["autism score 2", 2], ["autism score 3", 3], ["autism score 4", 4]]),
        protectionScores: new Map([["protection score 1", 5], ["protection score 2", 6], ["protection score 3", 7], ["protection score 4", 8]]),
        datasets: [1,2,3,4,5,6,7,8,9,10,11,12],
        // datasets: [{name: "SSC", affected: new Map([["LGD", 1],["MS", 2], ["SYN", 3]]), unaffected: new Map([["LGD", 4],["MS", 5], ["SYN", 6]])}],
      }
    ];
  }

  testButton1() {
    this.geneLists = ["gene list 1", "gene list 2"];
    // this.autismGeneProfilesService.getGenes().subscribe(res => console.log(res))
    this.autismGeneProfilesService.getConfig().subscribe(res => console.log(res))
  }

  testButton2() {
    this.geneLists = ["gene list 1", "gene list 2", "gene list 3", "gene list 4"];
  }
}
