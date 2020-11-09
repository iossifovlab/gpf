import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { GeneViewComponent, GeneViewZoomHistory, GeneViewScaleState } from './gene-view.component';

describe('GeneViewScaleState', () => {
  it('should have working getters', () => {
    const testScaleState = new GeneViewScaleState([1, 10], 5, 15, false);
    expect(testScaleState.xMin).toBe(1);
    expect(testScaleState.xMax).toBe(10);
  });
});

describe('GeneViewZoomHistory', () => {
  it('should add state to history', () => {
    const testZoomHistory = new GeneViewZoomHistory();

    const testScaleState1 = new GeneViewScaleState([1, 10], 5, 15, false);
    testZoomHistory.addStateToHistory(testScaleState1);
    expect(testZoomHistory.currentState).toEqual(testScaleState1);

    const testScaleState2 = new GeneViewScaleState([10, 20], 5, 25, false);
    testZoomHistory.addStateToHistory(testScaleState2);
    expect(testZoomHistory.currentState).toEqual(testScaleState2);
  });

  it('should check if index can go forward and backward', () => {
    const testScaleState = new GeneViewScaleState([1, 10], 5, 15, false);
    const testZoomHistory = new GeneViewZoomHistory();
    testZoomHistory.addStateToHistory(testScaleState);
    expect(testZoomHistory.canGoBackward).toBe(false);
    expect(testZoomHistory.canGoForward).toBe(false);
    testZoomHistory.addStateToHistory(testScaleState);
    expect(testZoomHistory.canGoBackward).toBe(true);
    expect(testZoomHistory.canGoForward).toBe(false);
  });

  it('should reset to default state', () => {
    const testScaleState1 = new GeneViewScaleState([1, 10], 5, 15, false);
    const testScaleState2 = new GeneViewScaleState([10, 20], 5, 25, false);
    const testZoomHistory = new GeneViewZoomHistory();
    testZoomHistory.addStateToHistory(testScaleState1);
    testZoomHistory.addStateToHistory(testScaleState2);

    const testDefaultState = new GeneViewScaleState([0, 0], 0, 0, false);
    testZoomHistory.resetToDefaultState(testDefaultState);
    expect(testZoomHistory.currentState).toEqual(testDefaultState);
    expect(testZoomHistory.canGoBackward).toBe(false);
    expect(testZoomHistory.canGoForward).toBe(false);
  });

  it('should move to previous and next states', () => {
    const testScaleState1 = new GeneViewScaleState([1, 10], 5, 15, false);
    const testScaleState2 = new GeneViewScaleState([10, 20], 5, 25, false);
    const testZoomHistory = new GeneViewZoomHistory();
    testZoomHistory.addStateToHistory(testScaleState1);
    testZoomHistory.addStateToHistory(testScaleState2);

    testZoomHistory.moveToPrevious();
    expect(testZoomHistory.currentState).toEqual(testScaleState1);
    testZoomHistory.moveToNext();
    expect(testZoomHistory.currentState).toEqual(testScaleState2);
  });
});
