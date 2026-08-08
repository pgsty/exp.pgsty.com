document.addEventListener("click", (event) => {
  const button =
    event.target instanceof Element
      ? event.target.closest("[data-pig-carousel-action]")
      : null;
  if (!button) return;

  const carousel = button.closest("[data-pig-carousel]");
  const track = carousel?.querySelector(".pig-doc-carousel-track");
  if (!track) return;

  const direction = button.dataset.pigCarouselAction === "previous" ? -1 : 1;
  const behavior = window.matchMedia("(prefers-reduced-motion: reduce)").matches
    ? "auto"
    : "smooth";
  track.scrollBy({ left: direction * track.clientWidth, behavior });
});
