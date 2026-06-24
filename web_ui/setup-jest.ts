import 'zone.js';
import 'zone.js/testing';
import '@angular/compiler';
import 'reflect-metadata';
import './jest-global-mocks';

import { getTestBed } from '@angular/core/testing';
import {
  BrowserDynamicTestingModule,
  platformBrowserDynamicTesting
} from '@angular/platform-browser-dynamic/testing';

getTestBed().initTestEnvironment(
  BrowserDynamicTestingModule,
  platformBrowserDynamicTesting()
);
