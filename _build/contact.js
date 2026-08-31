(function () {
  'use strict';

  var form = document.getElementById('inquiryForm');
  if (!form) return;
  var S = form.dataset;          // localized strings come from data-* on the form

  /* ── dictation ───────────────────────────────────────────── */
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

  /* ── submit ──────────────────────────────────────────────── */
  var supabaseClient = window.supabase.createClient(
    'https://kpqvfaqtxaglzaufqzcu.supabase.co',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtwcXZmYXF0eGFnbHphdWZxemN1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODIzNzM3MDMsImV4cCI6MjA5Nzk0OTcwM30.u0X9WybIZHBk260gdpFFSOd4qP6fLNjGAxEikPOEbSE'
  );

  form.addEventListener('submit', async function (e) {
    e.preventDefault();
    if (!form.checkValidity()) { form.reportValidity(); return; }

    var btn = document.getElementById('submitBtn');
    var btnText = document.getElementById('submitBtnText');
    var errorMsg = document.getElementById('errorMsg');

    var f = form.elements;
    var name = f.name.value.trim();
    var email = f.email.value.trim();
    var company = f.company.value.trim();
    var phone = f.phone.value.trim();
    var service = f.service.value;
    var details = f.details.value.trim();

    // the leads table has four columns — keep the extra fields inside description
    var description = details;
    var extra = [];
    if (company) extra.push('Company: ' + company);
    if (phone) extra.push('Phone: ' + phone);
    extra.push('Language: ' + (S.pageLang || 'en'));
    description += '\n\n---\n' + extra.join('\n');

    errorMsg.style.display = 'none';
    btn.disabled = true;
    btnText.textContent = S.sending || 'Sending…';

    var res = await supabaseClient.from('leads').insert({
      type: service, description: description, name: name, email: email
    });

    if (res.error) {
      console.error(res.error);
      btn.disabled = false;
      btnText.textContent = S.send || 'Send';
      errorMsg.style.display = 'block';
      return;
    }

    document.getElementById('formView').style.display = 'none';
    document.getElementById('successBox').style.display = 'block';
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
})();
