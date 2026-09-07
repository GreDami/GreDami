(function () {
  'use strict';

  var form = document.getElementById('inquiryForm');
  if (!form) return;
  var S = form.dataset;          // localized strings come from data-* on the form

  // Used to tell a person filling in a form from a script posting one. Read at
  // parse time, which is as close to "the page appeared" as this script gets.
  var OPENED = Date.now();

  /* ── dictation ───────────────────────────────────────────── */
  // Wrapped: dictation is a nicety, sending the form is not. If speech
  // recognition throws on some browser we have not seen, the submit handler
  // below must still be installed.
  try {
    (function () {
      var micBtn = document.getElementById('micBtn');
      var desc = document.getElementById('details');
      var micNote = document.getElementById('micNote');
      var micLangRow = document.getElementById('micLangRow');
      var langBtns = document.querySelectorAll('.mic-lang-btn');
      var Impl = window.SpeechRecognition || window.webkitSpeechRecognition;

      if (!Impl) { micBtn.hidden = true; micLangRow.hidden = true; return; }

      var LOCALES = { en: 'en-US', ru: 'ru-RU', fr: 'fr-FR', es: 'es-ES' };
      var NAMES = { en: S.langEn, ru: S.langRu, fr: S.langFr, es: S.langEs };
      var current = LOCALES[S.pageLang] ? S.pageLang : 'en';
      var recognition = null, listening = false, baseText = '', restart = false;

      function setActive() {
        langBtns.forEach(function (b) {
          b.classList.toggle('active', b.dataset.lang === current);
        });
      }
      setActive();

      langBtns.forEach(function (btn) {
        btn.addEventListener('click', function () {
          if (btn.dataset.lang === current) return;
          current = btn.dataset.lang;
          setActive();
          if (listening) { restart = true; recognition.stop(); }
        });
      });

      function start() {
        baseText = desc.value.trim() ? desc.value.trim() + ' ' : '';
        recognition = new Impl();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = LOCALES[current] || 'en-US';

        recognition.onstart = function () {
          listening = true;
          micBtn.classList.add('listening');
          micNote.textContent = (S.listening || '').replace('{lang}', NAMES[current] || current);
          micNote.style.display = 'block';
        };
        recognition.onresult = function (e) {
          var t = '';
          for (var i = 0; i < e.results.length; i++) t += e.results[i][0].transcript;
          desc.value = baseText + t;
        };
        recognition.onerror = function (e) { console.warn('Speech recognition:', e.error); };
        recognition.onend = function () {
          listening = false;
          micBtn.classList.remove('listening');
          micNote.style.display = 'none';
          if (restart) { restart = false; start(); }
        };
        recognition.start();
      }

      micBtn.addEventListener('click', function () {
        if (listening) recognition.stop(); else start();
      });
    })();
  } catch (err) {
    console.warn('Dictation unavailable:', err);
  }

  /* ── submit ──────────────────────────────────────────────── */
  var btn = document.getElementById('submitBtn');
  var btnText = document.getElementById('submitBtnText');
  var errorMsg = document.getElementById('errorMsg');

  function fail() {
    btn.disabled = false;
    btnText.textContent = S.send || 'Send';
    errorMsg.style.display = 'block';
    // A Turnstile token is single-use and expires; whatever went wrong, the
    // one in the form is spent. Without this a second attempt always fails.
    if (window.turnstile) { try { window.turnstile.reset(); } catch (e) { /* not rendered */ } }
  }

  form.addEventListener('submit', async function (e) {
    e.preventDefault();
    if (!form.checkValidity()) { form.reportValidity(); return; }

    var f = form.elements;
    var token = f['cf-turnstile-response'] ? f['cf-turnstile-response'].value : '';

    errorMsg.style.display = 'none';
    btn.disabled = true;
    btnText.textContent = S.sending || 'Sending…';

    // No token means Turnstile never ran — usually a blocker or a dead
    // network. The server would refuse it anyway; failing here saves a
    // round trip and shows the same message, which carries the email address.
    if (!token) { fail(); return; }

    var payload = {
      name: f.name.value.trim(),
      email: f.email.value.trim(),
      company: f.company.value.trim(),
      phone: f.phone.value.trim(),
      service: f.service.value,
      details: f.details.value.trim(),
      website: f.website ? f.website.value : '',   // honeypot: people leave it empty
      elapsed: Date.now() - OPENED,
      lang: S.pageLang || 'en',
      turnstile: token
    };

    var res;
    try {
      res = await fetch(S.endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    } catch (err) {
      // Offline, DNS, a blocked request. Without this the button sat disabled
      // on "Sending…" for ever and the person had nothing to act on.
      console.error('Contact form:', err);
      fail();
      return;
    }

    if (!res.ok) {
      console.error('Contact form:', res.status);
      fail();
      return;
    }

    document.getElementById('formView').style.display = 'none';
    var box = document.getElementById('successBox');
    box.style.display = 'block';
    window.scrollTo({ top: 0, behavior: 'smooth' });
    // The form it was reading has just been hidden, so a screen reader or a
    // keyboard is left with no position on the page. This is what the
    // tabindex="-1" on the box is for.
    box.focus();
  });
})();
