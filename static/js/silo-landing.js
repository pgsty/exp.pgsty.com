(function () {
  'use strict';

  var THEME_KEY = 'silo-landing-theme';
  var DARK_THEME_COLOR = '#0b1119';
  var LIGHT_THEME_COLOR = '#f1f4f8';
  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function currentTheme() {
    return document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
  }

  function storeTheme(theme) {
    try { window.localStorage.setItem(THEME_KEY, theme); } catch (error) {}
  }

  function applyTheme(theme) {
    var isLight = theme === 'light';
    document.documentElement.setAttribute('data-theme', theme);

    document.querySelectorAll('[data-theme-toggle]').forEach(function (button) {
      var label = isLight ? 'Switch to dark theme' : 'Switch to light theme';
      button.setAttribute('aria-label', label);
      button.setAttribute('title', label);
      button.setAttribute('data-active-theme', theme);
    });

    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute('content', isLight ? LIGHT_THEME_COLOR : DARK_THEME_COLOR);
  }

  function initTheme() {
    applyTheme(currentTheme());
    document.querySelectorAll('[data-theme-toggle]').forEach(function (button) {
      button.addEventListener('click', function () {
        var next = currentTheme() === 'light' ? 'dark' : 'light';
        applyTheme(next);
        storeTheme(next);
      });
    });
  }

  function legacyCopy(text) {
    var field = document.createElement('textarea');
    field.value = text;
    field.setAttribute('readonly', '');
    field.style.position = 'fixed';
    field.style.opacity = '0';
    field.style.pointerEvents = 'none';
    document.body.appendChild(field);
    field.select();
    var copied = false;
    try { copied = document.execCommand('copy'); } catch (error) {}
    document.body.removeChild(field);
    return copied;
  }

  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText && window.isSecureContext) {
      return navigator.clipboard.writeText(text).then(function () { return true; }).catch(function () {
        return legacyCopy(text);
      });
    }
    return Promise.resolve(legacyCopy(text));
  }

  function flashCopyButton(button, copied) {
    var original = button.innerHTML;
    button.innerHTML = copied ? '<span aria-hidden="true">✓</span> Copied' : '<span aria-hidden="true">!</span> Select manually';
    button.classList.toggle('copied', copied);
    window.setTimeout(function () {
      button.innerHTML = original;
      button.classList.remove('copied');
    }, 1800);
  }

  function initCopyButtons() {
    document.querySelectorAll('[data-copy-text]').forEach(function (button) {
      button.addEventListener('click', function () {
        copyText(button.getAttribute('data-copy-text') || '').then(function (copied) {
          flashCopyButton(button, copied);
        });
      });
    });

    document.querySelectorAll('[data-copy-target]').forEach(function (button) {
      button.addEventListener('click', function () {
        var target = document.querySelector(button.getAttribute('data-copy-target'));
        if (!target) return;
        copyText(target.textContent.trim()).then(function (copied) {
          flashCopyButton(button, copied);
        });
      });
    });
  }

  function initHeader() {
    var header = document.querySelector('[data-header]');
    if (!header) return;
    var update = function () {
      header.classList.toggle('scrolled', window.scrollY > 48);
    };
    window.addEventListener('scroll', update, { passive: true });
    update();
  }

  function initMobileMenu() {
    var toggle = document.querySelector('[data-menu-toggle]');
    var menu = document.querySelector('[data-mobile-menu]');
    if (!toggle || !menu) return;

    function setMenu(open) {
      toggle.classList.toggle('active', open);
      menu.classList.toggle('active', open);
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    }

    toggle.addEventListener('click', function () {
      setMenu(!menu.classList.contains('active'));
    });

    menu.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () { setMenu(false); });
    });

    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') setMenu(false);
    });

    document.addEventListener('click', function (event) {
      if (!menu.classList.contains('active')) return;
      if (menu.contains(event.target) || toggle.contains(event.target)) return;
      setMenu(false);
    });

    window.addEventListener('resize', function () {
      if (window.innerWidth > 900) setMenu(false);
    });
  }

  function initReveal() {
    var elements = document.querySelectorAll('[data-reveal]');
    if (!elements.length) return;

    if (reduceMotion || !('IntersectionObserver' in window)) {
      elements.forEach(function (element) { element.classList.add('revealed'); });
      return;
    }

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('revealed');
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.08, rootMargin: '0px 0px -36px 0px' });

    elements.forEach(function (element) { observer.observe(element); });
  }

  function init() {
    initTheme();
    initCopyButtons();
    initHeader();
    initMobileMenu();
    initReveal();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
