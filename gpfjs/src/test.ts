import './polyfills.ts';

import 'zone.js/dist/long-stack-trace-zone';
import 'zone.js/dist/proxy.js';
import 'zone.js/dist/sync-test';
import 'zone.js/dist/jasmine-patch';
import 'zone.js/dist/async-test';
import 'zone.js/dist/fake-async-test';
import { getTestBed } from '@angular/core/testing';
import {
  BrowserDynamicTestingModule,
  platformBrowserDynamicTesting
} from '@angular/platform-browser-dynamic/testing';

// Unfortunately there's no typing for the `__karma__` variable. Just declare it as any.
declare var __karma__: any;
declare var require: any;

// Prevent Karma from running prematurely.
__karma__.loaded = function () {};

// First, initialize the Angular testing environment.
getTestBed().initTestEnvironment(
  BrowserDynamicTestingModule,
  platformBrowserDynamicTesting()
);
// Then we find all the tests.
// let context = require.context('./', true, /\.spec\.ts$/);
const context = require.context(
  './', true,
  // tslint:disable-next-line:max-line-length
  /[^-]add-button\.component\.spec\.ts|[^-]genomic-scores\.component\.spec\.ts|[^-]genomic-scores-block\.component\.spec\.ts|[^-]pedigree-chart-member\.component\.spec\.ts|[^-]pedigree-chart\.component\.spec\.ts|[^-]genotype-preview-field\.component\.spec\.ts|[^-]subcontent\.component\.spec\.ts|[^-]content\.component\.spec\.ts|[^-]subheader\.component\.spec\.ts|[^-]header\.component\.spec\.ts|[^-]column\.component\.spec\.ts|[^-]cell\.component\.spec\.ts|[^-]empty-cell\.component\.spec\.ts|[^-]header-cell\.component\.spec\.ts/);
// And load the modules.
context.keys().map(context);
// Finally, start Karma to run the tests.
__karma__.start();
