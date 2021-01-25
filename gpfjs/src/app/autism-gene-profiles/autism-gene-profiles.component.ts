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
  private genes$: Observable<AutismGeneToolGene[]>;

  constructor(
    private autismGeneProfilesService: AutismGeneProfilesService,
  ) { }

  ngOnInit(): void {
    this.config$ = this.autismGeneProfilesService.getConfig();
    this.genes$ = this.autismGeneProfilesService.getGenes();

    this.config$.subscribe(res => {console.log(res); });
    this.genes$.subscribe(res => {console.log(res); });
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
    return datasetConfig.effects.length * datasetConfig.personSets.length;
  }

  testButton1() {
  }

  testButton2() {
  }

  log(val) { console.log(val); }
}
