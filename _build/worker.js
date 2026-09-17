/* gredami-lead — the contact form's only server.
 *
 * Deployed by hand into the Cloudflare dashboard (Workers & Pages →
 * gredami-lead → Edit code). It lives here so the code is in git: the
 * dashboard is where it runs, not where it is kept. Wrangler would do this
 * properly, but it drags in npm and node_modules, and this is not a node
 * project.
 *
 * The form on gredami.com posts here; this checks the request is human and
 * came from our own pages, then hands the message to Resend as email.
 * Nothing is stored. That is the point: the lead sits in a mailbox we control
 * from the moment it arrives, so no provider can pause or lock away the
 * archive — only the next submission.
 *
 * Set in Settings → Variables and Secrets:
 *   TURNSTILE_SECRET   secret
 *   RESEND_API_KEY     secret
 *   NOTIFY_TO          plain text — where the lead is mailed
 */

/* CabiStock's contact form (its /a-propos page) posts here too: the app is the
   studio's, and its correspondence belongs in the same inbox. Its host must
   also be listed on the Turnstile widget, or the token never gets issued. */
const ORIGINS = [
  'https://gredami.com',
  'https://www.gredami.com',
  'https://cabistock.gredami.workers.dev',
];

/* The values the forms send. The first six are the options on gredami.com,
   deliberately untranslated in build.py so a Spanish and a Russian enquiry
   arrive under the same name. `cabistock` is sent by the CabiStock form, which
   has no service picker, so its messages are recognisable in the subject line.
   Anything else means the payload was not built by one of our forms. */
const SERVICES = ['web', 'app', 'saas', 'design', 'growth', 'unsure', 'cabistock'];
const LANGS = ['en', 'fr', 'ru', 'es'];

const MAX = { name: 120, email: 200, company: 160, phone: 60, details: 8000 };

/* Nobody reads the page, thinks about their project and writes a brief in
   under three seconds. */
const MIN_FILL_MS = 3000;

function cors(origin) {
  return {
    'Access-Control-Allow-Origin': ORIGINS.includes(origin) ? origin : ORIGINS[0],
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '86400',
    'Vary': 'Origin',
  };
}

function json(body, status, origin) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', ...cors(origin) },
  });
}

function field(v, max) {
  return String(v == null ? '' : v).trim().slice(0, max);
}

/* Header injection is Resend's problem to prevent, not ours, but a subject
   line with a newline in it is malformed either way. */
function oneLine(s) {
  return s.replace(/[\r\n\t]+/g, ' ').trim();
}

/* Best-effort, and honestly labelled: a Worker isolate is not shared across
   colos and is recycled freely, so this catches a burst from one source
   rather than enforcing a real quota. Turnstile is the actual control; this
   only keeps a loop from turning into a mailbox full of identical messages.
   If it ever matters, swap it for a Rate Limiting binding. */
const recent = new Map();
function tooFast(ip) {
  const now = Date.now();
  for (const [k, t] of recent) if (now - t > 60000) recent.delete(k);
  const last = recent.get(ip);
  recent.set(ip, now);
  return last != null && now - last < 20000;
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin') || '';

    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: cors(origin) });
    }
    if (request.method !== 'POST') {
      return json({ error: 'method' }, 405, origin);
    }

    /* A page cannot forge its own Origin, so this stops the form being driven
       from somebody else's site. It does nothing against curl — that is what
       Turnstile is for. */
    if (!ORIGINS.includes(origin)) {
      return json({ error: 'origin' }, 403, origin);
    }

    let data;
    try {
      data = await request.json();
    } catch {
      return json({ error: 'json' }, 400, origin);
    }

    /* Both of these answer 200. A bot that is told it was caught learns what
       to change; one that is thanked goes away satisfied. */
    if (field(data.website, 200) !== '') {
      return json({ ok: true }, 200, origin);
    }
    if (!(Number(data.elapsed) >= MIN_FILL_MS)) {
      return json({ ok: true }, 200, origin);
    }

    const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
    if (tooFast(ip)) {
      return json({ error: 'rate' }, 429, origin);
    }

    let check;
    try {
      const res = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          secret: env.TURNSTILE_SECRET,
          response: field(data.turnstile, 4096),
          remoteip: ip,
        }),
      });
      check = await res.json();
    } catch (err) {
      console.error('turnstile unreachable', err);
      return json({ error: 'turnstile' }, 502, origin);
    }
    if (!check || check.success !== true) {
      console.warn('turnstile rejected', check && check['error-codes']);
      return json({ error: 'turnstile' }, 403, origin);
    }

    const name = field(data.name, MAX.name);
    const email = field(data.email, MAX.email);
    const company = field(data.company, MAX.company);
    const phone = field(data.phone, MAX.phone);
    const details = field(data.details, MAX.details);
    const service = SERVICES.includes(data.service) ? data.service : 'unsure';
    const lang = LANGS.includes(data.lang) ? data.lang : 'en';

    /* The browser has already enforced all of this; a request that reaches
       here failing it did not come from the form. */
    if (!name || !email || details.length < 10) {
      return json({ error: 'fields' }, 400, origin);
    }
    if (!/^[^@\s]+@[^@\s.]+\.[^@\s]{2,}$/.test(email)) {
      return json({ error: 'email' }, 400, origin);
    }

    const subject = oneLine(`[${service}] ${name}${company ? ' — ' + company : ''}`);

    const lines = [
      `Name:     ${name}`,
      `Email:    ${email}`,
      company ? `Company:  ${company}` : null,
      phone ? `Phone:    ${phone}` : null,
      `Service:  ${service}`,
      `Language: ${lang}`,
      '',
      '---',
      '',
      details,
    ].filter((l) => l !== null);

    let send;
    try {
      send = await fetch('https://api.resend.com/emails', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${env.RESEND_API_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          from: 'GreDami <form@send.gredami.com>',
          to: [env.NOTIFY_TO],
          /* So hitting reply in the mail client answers the person who wrote,
             not the sending domain. */
          reply_to: email,
          subject,
          text: lines.join('\n'),
        }),
      });
    } catch (err) {
      console.error('resend unreachable', err);
      return json({ error: 'send' }, 502, origin);
    }

    if (!send.ok) {
      console.error('resend', send.status, await send.text());
      return json({ error: 'send' }, 502, origin);
    }

    return json({ ok: true }, 200, origin);
  },
};
