import { Component, OnInit } from '@angular/core';
import { AutismGeneToolConfig, AutismGeneToolGene } from './autism-gene-profile';
import { AutismGeneProfilesService } from './autism-gene-profiles.service';

@Component({
  selector: 'gpf-autism-gene-profiles',
  templateUrl: './autism-gene-profiles.component.html',
  styleUrls: ['./autism-gene-profiles.component.css']
})
export class AutismGeneProfilesComponent implements OnInit {
  private config: AutismGeneToolConfig;
  private genes: AutismGeneToolGene[];

  constructor(
    private autismGeneProfilesService: AutismGeneProfilesService,
  ) { }

  ngOnInit(): void {
    this.autismGeneProfilesService.getConfig().subscribe(config => this.config = config);
    this.autismGeneProfilesService.getGenes().subscribe(genes => this.genes = genes);
  }

  testButton1() {
  }

  testButton2() {

  }
}
