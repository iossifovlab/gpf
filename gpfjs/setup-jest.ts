import 'jest-preset-angular/setup-jest';
import 'reflect-metadata';
import './jest-global-mocks';
import * as $ from 'jquery';
Object.defineProperty(window, '$', {value: $});
Object.defineProperty(global, '$', {value: $});
Object.defineProperty(global, 'jQuery', {value: $});
import 'jquery-ui/dist/jquery-ui';
