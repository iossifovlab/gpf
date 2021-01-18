import { Component, OnInit } from '@angular/core';

// class GeneRow {
//   constructor(
//     public name: String,
//     public geneLists: Map<String, Boolean>,
//     public autismScores: Map<String, Number>,
//     public protectionScores: Map<String, Number>,
//     public datasets: {name: String, data: Map<String, Number>}[]
//   ) { }
// }

@Component({
  selector: 'gpf-autism-gene-profiles',
  templateUrl: './autism-gene-profiles.component.html',
  styleUrls: ['./autism-gene-profiles.component.css']
})
export class AutismGeneProfilesComponent implements OnInit {
  // geneRows: GeneRow[];

  // constructor() {
  //   this.geneRows = new Array<GeneRow>();
  // }

  ngOnInit(): void {
    // const allGeneNames = this.getGeneNames();
    // const allGeneLists = this.getGeneLists();
    // const allAutismScores = this.getAutismScores();
    // const allProtectionScores = this.getProtectionScores();
    // const allDatasets = this.getDatasets();

    // for (let geneName in allGeneNames) {
    //   this.geneRows.push(
    //     new GeneRow(
    //       geneName,
    //       allGeneLists.get(geneName),
    //       allAutismScores.get(geneName),
    //       allProtectionScores.get(geneName),
    //       allDatasets.get(geneName)
    //     )
    //   );
    // }
    
  }

  // getGeneNames():  {
  //   ///
  // }

  // getGeneLists() {
  //   ///
  // }
  
  // getAutismScores() {
  //  /// 
  // }

  // getProtectionScores() {
  //  /// 
  // }

  // getDatasets() {
  //   /// 
  // }
}
