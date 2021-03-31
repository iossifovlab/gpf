import { BasePage } from './utils';

export class ShareQueryPage extends BasePage {
  get button() {
    return cy.get('#share-query-dropdown-button');
  }

  get dropdownMenu() {
    return cy.get('#share-query-dropdown');
  }

  get input() {
    return cy.get('div#share-query-dropdown input');
  }

//   async waitForShareQueryInput() {
//     const promise = new Promise<void>((resolve) => {
//       setTimeout(async () => {
//         if (await this.input.getAttribute('value') !== '') {
//           resolve();
//         }
//       }, 5000);
//     });

//    return promise;
//   }
}
