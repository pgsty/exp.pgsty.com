document.addEventListener("click", (event) => {
  const button =
    event.target instanceof Element
      ? event.target.closest("[data-silo-carousel-action]")
      : null;
  if (!button) return;

  const carousel = button.closest("[data-silo-carousel]");
  const track = carousel?.querySelector(".silo-doc-carousel-track");
  if (!track) return;

  const direction = button.dataset.siloCarouselAction === "previous" ? -1 : 1;
  const behavior = window.matchMedia("(prefers-reduced-motion: reduce)").matches
    ? "auto"
    : "smooth";
  track.scrollBy({ left: direction * track.clientWidth, behavior });
});
