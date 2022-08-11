export function isInViewport(el, percentVisible) {
    let rect = el.getBoundingClientRect(),
        windowHeight = (window.innerHeight || document.documentElement.clientHeight);

    return !(
        Math.floor(100 - (((rect.top >= 0 ? 0 : rect.top) / +-rect.height) * 100)) < percentVisible ||
        Math.floor(100 - ((rect.bottom - windowHeight) / rect.height) * 100) < percentVisible
    )
}
