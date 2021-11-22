import { BaseType, Selection } from "d3-selection";

export const affectedStatusColors = {
  'Affected only': '#AA0000',
  'Unaffected only': '#04613a',
  'Affected and unaffected': '#8a8a8a',
};

function getTrianglePoints(plotX: number, plotY: number, size: number) {
  const height = Math.sqrt(Math.pow(size, 2) - Math.pow((size / 2.0), 2));
  const x1 = plotX - (size / 2.0);
  const y1 = plotY + (height / 2.0);
  const x2 = plotX + (size / 2.0);
  const y2 = plotY + (height / 2.0);
  const x3 = plotX;
  const y3 = plotY - (height / 2.0);
  return `${x1},${y1} ${x2},${y2} ${x3},${y3}`;
}

export function hoverText(element: Selection<BaseType, unknown, HTMLElement, any>, x: number, y: number, text: string, svgTitle: string, fontSize: number) {
  element.append('text')
    .attr('x', x)
    .attr('y', y)
    .attr('font-size', `${fontSize}px`)
    .text(text)
    .attr('cursor', 'default')
    .attr('text-anchor', 'end')
    .append('svg:title').text(`${svgTitle}`);
}

export function surroundingRectangle(
    element: Selection<BaseType, unknown, HTMLElement, any>, x: number, y: number, color: string, title: string,
    strokeOpacity: number = 1, w: number = 16
  ) {
  const h = 16;
  element.append('g')
    .append('rect')
    .attr('x', x - w / 2)
    .attr('y', y - h / 2)
    .attr('width', w)
    .attr('height', h)
    .style('fill', color)
    .style('fill-opacity', 0.2)
    .style('stroke', color)
    .style('stroke-width', 2)
    .style('stroke-opacity', strokeOpacity)
    .append('svg:title').text(title);
}

export function star(element: Selection<BaseType, unknown, HTMLElement, any>, x: number, y: number, color: string, title: string) {
  element.append('svg')
    .attr('x', x - 8.5)
    .attr('y', y - 8.5)
    .append('g')
    .append('path')
    .attr('d', 'M12 .587l3.668 7.568 8.332 1.151-6.064 5.828 1.48 8.279-7.416-3.967-7.417 3.967 1.481-8.279-6.064-5.828 8.332-1.151z')
    .attr('transform', 'scale(0.7)')
    .attr('fill', color)
    .attr('fill-opacity', '0.6')
    .style('stroke-width', 1)
    .style('stroke', color)
    .append('svg:title').text(title);
}

export function triangle(element: Selection<BaseType, unknown, HTMLElement, any>, x: number, y: number, color: string, title: string) {
  element.append('g')
    .append('polygon')
    .attr('points', getTrianglePoints(x, y, 14))
    .style('fill', color)
    .attr('fill-opacity', '0.6')
    .style('stroke-width', 1)
    .style('stroke', color)
    .append('svg:title').text(title);
}

export function circle(element: Selection<BaseType, unknown, HTMLElement, any>, x: number, y: number, color: string, title: string, radius: number = 7) {
  element.append('g')
    .append('circle')
    .attr('cx', x)
    .attr('cy', y)
    .attr('r', radius)
    .style('fill', color)
    .attr('fill-opacity', '0.6')
    .style('stroke-width', 1)
    .style('stroke', color)
    .append('svg:title').text(title);
}

export function dot(element: Selection<BaseType, unknown, HTMLElement, any>, x: number, y: number, color: string, title: string) {
    circle(element, x, y, color, title, 3);
}

export function rect(element: Selection<BaseType, unknown, HTMLElement, any>, xStart: number, xEnd: number, y: number, height: number, color: string, opacity: number, title: string) {
  element.append('rect')
    .attr('height', height)
    .attr('width', xEnd - xStart)
    .attr('x', xStart)
    .attr('y', y)
    .style('fill', color)
    .attr('fill-opacity', opacity)
    .attr('stroke', color)
    .style('stroke-opacity', opacity)
    .append('svg:title').text(title);
}

export function line(element: Selection<BaseType, unknown, HTMLElement, any>, xStart: number, xEnd: number, y: number, svgTitle: string) {
  element.append('line')
    .attr('x1', xStart)
    .attr('y1', y)
    .attr('x2', xEnd)
    .attr('y2', y)
    .attr('stroke', 'black')
    .append('svg:title').text(svgTitle);
}
