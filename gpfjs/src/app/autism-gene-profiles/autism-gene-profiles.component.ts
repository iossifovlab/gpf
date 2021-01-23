import { AfterViewInit, Component, OnInit } from '@angular/core';
import { Observable } from 'rxjs';
import { AutismGeneToolConfig, AutismGeneToolGene } from './autism-gene-profile';
import { AutismGeneProfilesService } from './autism-gene-profiles.service';

@Component({
  selector: 'gpf-autism-gene-profiles',
  templateUrl: './autism-gene-profiles.component.html',
  styleUrls: ['./autism-gene-profiles.component.css']
})
export class AutismGeneProfilesComponent implements OnInit {
  private config$: Observable<AutismGeneToolConfig>;
  private genes: AutismGeneToolGene[];

  constructor(
    private autismGeneProfilesService: AutismGeneProfilesService,
  ) { }

  ngOnInit(): void {
    this.config$ = this.autismGeneProfilesService.getConfig();
    this.autismGeneProfilesService.getGenes().subscribe(genes => this.genes = genes);

    this.config$.subscribe(res => {console.log(res); });
    this.autismGeneProfilesService.getGenes().subscribe(genes => {console.log(genes); });
  }

  // getDatasetsNamesArray() {
  //   this.config$.subscribe(conf => {
  //     return conf.datasets.map(dataset => dataset.name);
  //   });
  // }

  // getDatasetConfigByName(datasetName: string) {
  //   this.config$.subscribe(conf => {
  //     return conf.datasets.find(dataset => dataset.name === datasetName);
  //   });
  // }

  calculateDatasetColspan(datasetConfig) {
    console.log(datasetConfig.effects.length * datasetConfig.personSets.length)
    return datasetConfig.effects.length * datasetConfig.personSets.length;
  }

  testButton1() {
  }

  testButton2() {
  }

  log(val) { console.log(val); }
}
