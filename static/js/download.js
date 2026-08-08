/**
 * SILO download page interactions:
 * accessible install-method tabs, copy controls, and platform hinting.
 */
(function () {
  'use strict';

  function writeClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text);
    }

    return new Promise(function (resolve, reject) {
      var textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.setAttribute('readonly', '');
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();

      try {
        if (!document.execCommand('copy')) throw new Error('copy failed');
        resolve();
      } catch (error) {
        reject(error);
      } finally {
        document.body.removeChild(textarea);
      }
    });
  }

  function flashCopied(button) {
    var original = button.innerHTML;
    button.classList.add('copied');
    button.innerHTML = '<i class="fas fa-check" aria-hidden="true"></i><b>' +
      (document.documentElement.lang.indexOf('zh') === 0 ? '已复制' : 'Copied') +
      '</b>';

    window.setTimeout(function () {
      button.innerHTML = original;
      button.classList.remove('copied');
    }, 1500);
  }

  function initCopyControls() {
    document.querySelectorAll('[data-copy-command]').forEach(function (button) {
      button.addEventListener('click', function () {
        var block = button.closest('.download-code');
        var code = block && block.querySelector('pre code');
        if (!code) return;
        writeClipboard(code.textContent.trim()).then(function () {
          flashCopied(button);
        }).catch(function () {});
      });
    });

    document.querySelectorAll('[data-copy-inline]').forEach(function (button) {
      button.addEventListener('click', function () {
        var row = button.closest('.client-quick-command');
        var code = row && row.querySelector('code');
        if (!code) return;
        writeClipboard(code.textContent.trim()).then(function () {
          flashCopied(button);
        }).catch(function () {});
      });
    });
  }

  function activateTab(group, targetId, updateHash) {
    var button = group.querySelector('[data-download-tab="' + targetId + '"]');
    var panel = group.querySelector('#' + targetId);
    if (!button || !panel) return false;

    group.querySelectorAll('[data-download-tab]').forEach(function (item) {
      var active = item === button;
      item.setAttribute('aria-selected', active ? 'true' : 'false');
      item.setAttribute('tabindex', active ? '0' : '-1');
    });

    group.querySelectorAll('[role="tabpanel"]').forEach(function (item) {
      item.hidden = item !== panel;
    });

    if (updateHash && window.history && window.history.replaceState) {
      window.history.replaceState(null, '', '#' + targetId);
    }
    return true;
  }

  function initTabs() {
    var groups = Array.prototype.slice.call(document.querySelectorAll('[data-download-tabs]'));

    groups.forEach(function (group) {
      var buttons = Array.prototype.slice.call(group.querySelectorAll('[data-download-tab]'));

      buttons.forEach(function (button, index) {
        button.addEventListener('click', function () {
          activateTab(group, button.dataset.downloadTab, true);
        });

        button.addEventListener('keydown', function (event) {
          var nextIndex = null;
          if (event.key === 'ArrowRight') nextIndex = (index + 1) % buttons.length;
          if (event.key === 'ArrowLeft') nextIndex = (index - 1 + buttons.length) % buttons.length;
          if (event.key === 'Home') nextIndex = 0;
          if (event.key === 'End') nextIndex = buttons.length - 1;
          if (nextIndex === null) return;

          event.preventDefault();
          var next = buttons[nextIndex];
          activateTab(group, next.dataset.downloadTab, true);
          next.focus();
        });
      });
    });

    var hash = window.location.hash.slice(1);
    if (!hash) return;

    for (var i = 0; i < groups.length; i += 1) {
      if (!activateTab(groups[i], hash, false)) continue;
      window.requestAnimationFrame(function () {
        var target = document.getElementById(hash);
        var tabs = target && target.closest('[data-download-tabs]');
        if (tabs) tabs.scrollIntoView({ block: 'start' });
      });
      break;
    }
  }

  function initPlatformHint() {
    var source = ((navigator.userAgent || '') + ' ' + (navigator.platform || '')).toLowerCase();
    var platform = '';

    if (source.indexOf('win') !== -1) platform = 'windows';
    else if (source.indexOf('mac') !== -1) platform = 'macos';
    else if (source.indexOf('linux') !== -1) platform = 'linux';

    if (!platform) return;
    document.querySelectorAll('[data-platform="' + platform + '"]').forEach(function (card) {
      card.classList.add('detected-platform');
    });
  }

  function init() {
    initTabs();
    initCopyControls();
    initPlatformHint();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
