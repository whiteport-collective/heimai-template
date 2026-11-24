#!/usr/bin/env node
// The Heim runner: one program, used by the Lighthouse agents on their rounds and by the Watchdog
// twice a day. It reads every process file in the Heim's processes folder, runs the script at its end,
// and updates the whole timeline: points whose date has passed become consequences, the history gets
// a row, and timeline.json (what the glass reads) is rewritten. Safe to run twice: it checks the
// history before it writes. No dependencies.
//
//   node heim-run.mjs [--root <heim folder>] [--by watchdog|lighthouse] [--today YYYY-MM-DD] [--dry]
//
// Where the processes and the runner's own files lie comes from the Heim's floor plan:
// `.heimai/heimai.yaml` (`heimai: 2`), where the processes are in `.heimai/tasks/` and the timeline in
// `.heimai/machine/` unless `tasks:` and `machine:` say otherwise; or, until the Heim is moved, the root
// `heim.yaml` (`heim: 1`), where they are in `tasks/` and `.heim/`.
//
// Every Heim inside the root (a folder with its own floor plan and processes folder, such as a project)
// is run after it, the same way; `--nested` is that inner run, which runs no further Heims itself.
//
// The formats are documented in HeimAI's docs/reference/: process-files.md and recurring-processes.md.

import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';

const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
const ROOT = path.resolve(opt('--root', '.'));
const BY = opt('--by', 'lighthouse');
const DRY = args.includes('--dry');
const TODAY = opt('--today', new Intl.DateTimeFormat('sv-SE', { timeZone: 'Europe/Stockholm' }).format(new Date()));
const LIGHTHOUSE_MAX_HOURS = 26;

const DATE = /\b(\d{4}-\d{2}-\d{2})\b/;

// ── The floor plan ──────────────────────────────────────────────────────
// The runner has no dependencies, so it reads only the top-level keys it needs: a value, or a list.
const unquote = (v) => v.trim().replace(/^(["'])(.*)\1$/, '$2');
function topKeys(text) {
  const out = {}; let list = null;
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.replace(/\s+#.*$/, '').replace(/^#.*$/, '');
    if (!line.trim()) continue;
    const m = line.match(/^([A-Za-z_][\w-]*):\s*(.*)$/);
    if (m) {
      const v = m[2].trim();
      if (!v) list = out[m[1]] = [];
      else { list = null; out[m[1]] = v.startsWith('[') ? v.replace(/^\[|\]$/g, '').split(',').map(unquote).filter(Boolean) : unquote(v); }
      continue;
    }
    const item = line.match(/^\s+-\s+(.*)$/);
    if (item && list) list.push(unquote(item[1]));
  }
  return out;
}
const asFolder = (v) => { const s = String(v).trim().replace(/^\.?\//, ''); return s && s !== '.' ? s.replace(/\/*$/, '/') : ''; };
// Where the processes lie: the first `tasks:` pattern that is a folder, else the folder the patterns
// share up to their first wildcard (the same rule as the Open Glass).
function processFolder(patterns) {
  const folderPattern = patterns.find((p) => p.endsWith('/') && !/[*?[]/.test(p));
  if (folderPattern) return folderPattern;
  const dirs = patterns.map((p) => { const lit = p.split(/[*?[]/)[0]; return lit.slice(0, lit.lastIndexOf('/') + 1); });
  let common = dirs[0] ?? '';
  for (const d of dirs.slice(1)) while (!d.startsWith(common)) common = common.slice(0, common.slice(0, -1).lastIndexOf('/') + 1);
  return common;
}
/** A Heim's floor plan as the runner needs it, every path relative to its root. */
function planOf(root) {
  // A Heim that lies inside a `.heimai/` folder has its floor plan and its folders right in its root.
  const inside = root.split(/[\\/]/).includes('.heimai');
  const v2 = inside && fs.existsSync(path.join(root, 'heimai.yaml')) ? path.join(root, 'heimai.yaml') : path.join(root, '.heimai', 'heimai.yaml');
  if (fs.existsSync(v2)) {
    const keys = topKeys(fs.readFileSync(v2, 'utf8'));
    const home = inside ? '' : '.heimai/';
    const tasks = [].concat(keys.tasks ?? []).filter((t) => typeof t === 'string' && t).map((t) => t.replace(/^\.?\//, ''));
    const tasksDir = processFolder(tasks.length ? tasks : [`${home}tasks/`]) || `${home}tasks/`;
    const machine = typeof keys.machine === 'string' ? asFolder(keys.machine) : `${home}machine/`;
    return { format: 2, tasksDir, machine, notify: `${machine}notify.txt`, lighthouse: typeof keys.lighthouse === 'string' && !!keys.lighthouse };
  }
  const heimYaml = fs.existsSync(path.join(root, 'heim.yaml')) ? fs.readFileSync(path.join(root, 'heim.yaml'), 'utf8') : '';
  return { format: 1, tasksDir: 'tasks/', machine: '.heim/', notify: '.heim-notify.txt', lighthouse: /^lighthouse:\s*\S/m.test(heimYaml), exists: !!heimYaml };
}
const PLAN = planOf(ROOT);
const TASKS = path.join(ROOT, PLAN.tasksDir);
const days = (a, b) => Math.round((Date.parse(b) - Date.parse(a)) / 86400000);

// ── Reading a process file ──────────────────────────────────────────────
function sections(text) {
  const out = { _head: [] }; let cur = '_head';
  for (const line of text.split(/\r?\n/)) {
    const m = line.match(/^## (.+?)\s*$/);
    if (m) { cur = m[1].toLowerCase(); out[cur] = []; continue; }
    out[cur].push(line);
  }
  return out;
}
function table(lines = []) {
  const rows = lines.filter((l) => l.trim().startsWith('|'));
  if (rows.length < 2) return { header: [], rows: [] };
  const cells = (l) => l.trim().replace(/^\||\|$/g, '').split('|').map((c) => c.trim());
  return { header: cells(rows[0]), rows: rows.slice(2).map(cells) };
}
function runScript(code, file) {
  const m = code.match(/```js\s*([\s\S]*?)```/);
  if (!m) return {};
  const src = m[1].replace(/export\s+default/, 'module.exports =');
  const sandbox = { module: { exports: {} } };
  try { vm.runInNewContext(src, sandbox, { timeout: 2000, filename: file }); }
  catch (e) { return { _error: String(e.message || e) }; }
  return sandbox.module.exports || {};
}
function readProcess(file) {
  const text = fs.readFileSync(file, 'utf8');
  const s = sections(text);
  const title = (s._head.find((l) => l.startsWith('# ')) || '').slice(2).trim();
  const meta = s._head.find((l) => /Field:|Owner:/.test(l)) || '';
  const field = (meta.match(/Field:\s*([^·]+)/) || [])[1]?.trim() || null;
  const owner = (meta.match(/Owner:\s*([^·]+)/) || [])[1]?.trim() || null;
  const points = table(s.points);
  const history = table(s.history);
  const script = runScript((s.script || []).join('\n'), file);
  // The plan (`## Steps`, a numbered list) and the log of steps done (`## Log`).
  const steps = (s.steps || []).map((l) => l.match(/^\s*(?:\d+[.)]|[-*])\s+(.+?)\s*$/)?.[1]).filter(Boolean);
  const log = table(s.log);
  // What an agent prepared for a step of a run (`| Run | Step | Text |`): today's affirmation.
  const texts = table(s.texts);
  // The invoices that have come and are not paid (`## Open invoices`), each with its own amount, OCR
  // and due date, since those change from invoice to invoice.
  const invoices = table(s['open invoices']);
  return { file, text, title, field, owner, points, history, script, steps, log, texts, invoices };
}

/** The open invoices of a thread, `| Invoice | Amount | OCR | Due | Mail |`: the row is removed when it is paid. */
function invoicesOf(p) {
  const { header, rows } = p.invoices;
  const col = (re) => header.findIndex((h) => re.test(h));
  const [iInv, iAmount, iOcr, iDue, iMail] = [/invoice/i, /amount/i, /ocr|message/i, /due/i, /^mail$/i].map(col);
  const cell = (r, i) => (i >= 0 ? (r[i] || '').replace(/`/g, '').trim() : '');
  return rows
    .map((r) => ({
      invoice: cell(r, iInv) || null,
      amount: Number(cell(r, iAmount).replace(/[^\d,.-]/g, '').replace(',', '.')) || null,
      ocr: cell(r, iOcr) || null,
      due: cell(r, iDue).match(DATE)?.[1] || null,
      ...(cell(r, iMail) && { mail: cell(r, iMail) }),
    }))
    .filter((x) => x.invoice || x.amount || x.ocr);
}

// ── Sub-threads: a plan run step by step ────────────────────────────────
// A thread with `## Steps` is run after its plan; `## Log` has a row per step done,
// `| Time | Run | Step | Note |`. Each run becomes a sub-thread in the timeline: the plan's steps
// in order, each `done` at its time or `open`. A routine's run is its day.
function runsOf(p, routineDays) {
  if (!p.steps.length) return null;
  const h = p.log.header;
  const iTime = h.findIndex((x) => /time/i.test(x));
  const iRun = h.findIndex((x) => /run/i.test(x));
  const iStep = h.findIndex((x) => /step/i.test(x));
  const stepOf = (cell = '') => {
    const c = cell.trim().toLowerCase();
    const byName = p.steps.findIndex((s) => s.toLowerCase() === c);
    if (byName >= 0) return byName;
    const n = parseInt(c, 10);
    return n >= 1 && n <= p.steps.length ? n - 1 : -1;
  };
  const byRun = new Map();
  for (const r of p.log.rows) {
    const at = (r[iTime] || '').match(/(\d{4}-\d{2}-\d{2})[ T](\d{1,2}:\d{2})/);
    const run = (r[iRun] || '').trim() || at?.[1];
    const i = stepOf(r[iStep]);
    if (!run || i < 0) continue;
    if (!byRun.has(run)) byRun.set(run, new Map());
    // The first time a step was done counts; a second row for it changes nothing.
    if (!byRun.get(run).has(i)) byRun.get(run).set(i, at ? `${at[1]} ${at[2].padStart(5, '0')}` : null);
  }
  const t = p.texts.header;
  const tRun = t.findIndex((x) => /run/i.test(x));
  const tStep = t.findIndex((x) => /step/i.test(x));
  const tText = t.findIndex((x) => /text/i.test(x));
  const textOf = new Map();
  for (const r of p.texts.rows) {
    const i = stepOf(r[tStep]);
    if (r[tRun] && i >= 0 && r[tText]) textOf.set(`${r[tRun].trim()}#${i}`, r[tText]);
  }
  // A routine: a run for each day in the log or done, and today's. Anything else: the runs in the log.
  const names = routineDays
    ? [...new Set([...byRun.keys(), ...routineDays])].filter((d) => /^\d{4}-\d{2}-\d{2}$/.test(d) && d <= TODAY).sort()
    : [...byRun.keys()];
  const runs = names.map((run) => {
    const done = byRun.get(run) || new Map();
    const steps = p.steps.map((name, i) => ({ n: i + 1, name, status: done.has(i) ? 'done' : 'open', at: done.get(i) || null,
      ...(textOf.has(`${run}#${i}`) && { text: textOf.get(`${run}#${i}`) }) }));
    return { run, steps, done: steps.every((s) => s.status === 'done') };
  });
  // The current run: today's for a routine, else the last one not finished.
  const current = routineDays ? TODAY : [...runs].reverse().find((r) => !r.done)?.run || null;
  // The step a routine's values are answered in: `measuredIn` in the script, else the plan's last.
  const m = Number(p.script.measuredIn);
  const measuredIn = p.script.measure ? (m >= 1 && m <= p.steps.length ? m : p.steps.length) : null;
  return { steps: p.steps, runs, current, measuredIn };
}

// ── Recurring threads: subscriptions, loans, credits ────────────────────
// A thread whose script says `every` is something that comes back: a bill, a draw, a credit card.
// The runner lays out its points a year ahead, so the glass only draws:
//   draw     money leaves the account on a set day (a loan, autogiro): the point the day before
//            says how much must be on which account
//   invoice  an invoice arrives, then falls due: two points per period
//   credit   like an invoice, plus the interest worked out from the balance and the rate, so it
//            is never invisible
//   card     charged to a card on a set day: one point, no money needed on an account first
//   income   money that should come in on a set day (a lodger's rent): one point, `Expected`.
//            It is laid out from `since` (the first one), not only from today, so a month that
//            never came stays visible. A past point with no history row near it is `missed` when
//            it is on or before `checked` (the last day the bank exports were read through), else
//            `unconfirmed`. What came in pays the oldest month first, so a late or partial payment
//            counts where it belongs and what is owed is one sum (`owed`), a consequence of the thread.
//            It is never in `cash`.
// The script's keys: kind, every ('month' | 'quarter' | 'year' | 'N months'), months (which
// months, for quarterly and yearly), on (the day it is drawn or due, or 'last'), arrives (the day
// the invoice comes), amount, account, pay ({bg|pg, ocr}), balance, rate (yearly %), payment
// (what is paid each month on a credit), until (last date), priority (1 first), and for income
// since (the first date) and checked (the bank exports were read through this date). Any kind may
// have changes: [{ from: 'YYYY-MM-DD', amount }], an amount that holds from that date on.
// A past point is `done` when the history has a row near it, else `unconfirmed`: the bank export
// may simply not reach that far, so a missing row is never reported as missed.

const HORIZON_MONTHS = 12;
const iso = (d) => d.toISOString().slice(0, 10);
const utc = (y, m, d) => new Date(Date.UTC(y, m, d));
const lastDay = (y, m) => utc(y, m + 1, 0).getUTCDate();
/** Saturday or Sunday moves to Monday: banks draw and register on bank days. */
const bankDay = (d) => { const w = d.getUTCDay(); return w === 6 ? utc(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate() + 2) : w === 0 ? utc(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate() + 1) : d; };
const dayIn = (y, m, day) => utc(y, m, day === 'last' ? lastDay(y, m) : Math.min(Number(day) || 1, lastDay(y, m)));
const kr = (n) => `${Math.round(n).toLocaleString('sv-SE')} kr`;

function periodMonths(sc) {
  if (Array.isArray(sc.months) && sc.months.length) return sc.months.map(Number);
  const every = String(sc.every || 'month');
  const n = every === 'quarter' ? 3 : every === 'year' ? 12 : parseInt(every, 10) || 1;
  return Array.from({ length: 12 }, (_, i) => i + 1).filter((m) => (m - 1) % n === 0);
}

/** Every history row with a date and an amount. */
function historyRows(p) {
  const iDate = p.history.header.findIndex((h) => /date/i.test(h));
  const iWhat = p.history.header.findIndex((h) => /what/i.test(h));
  const iAmount = p.history.header.findIndex((h) => /amount/i.test(h));
  // The receipt behind a row (a file on the drive), or "missing": only where the thread keeps them.
  const iReceipt = p.history.header.findIndex((h) => /receipt/i.test(h));
  // The mail behind a row, `[<summary>](<mail link>)`, carried as it is.
  const iMail = p.history.header.findIndex((h) => /^mail$/i.test(h));
  return p.history.rows.map((r) => ({
    date: (r[iDate] || '').match(DATE)?.[1],
    what: r[iWhat] || '',
    amount: iAmount >= 0 ? Number(String(r[iAmount]).replace(/[^\d,.-]/g, '').replace(',', '.')) || null : null,
    // Only the word "missing" says a receipt is missing; an empty cell makes no claim.
    ...(iReceipt >= 0 && r[iReceipt] && { receipt: /^missing$/i.test(r[iReceipt]) ? null : r[iReceipt] }),
    ...(iMail >= 0 && r[iMail] && { mail: r[iMail] }),
  })).filter((r) => r.date);
}

/**
 * A credit's way to zero (a curve that only goes down, since zero is good): the balance after
 * each period from today, with the interest and the
 * payment, until it is paid or ten years have passed, so the glass draws the whole curve and
 * computes nothing. A credit nobody pays down (an overdraft) is laid out over the horizon only.
 */
function creditPlan(sc, months) {
  const today = new Date(`${TODAY}T00:00:00Z`);
  const rate = (Number(sc.rate) || 0) / 100 / months.length;
  const payment = Number(sc.payment) || Number(sc.amount) || 0;
  let balance = Number(sc.balance) || 0;
  const plan = [{ date: TODAY, balance: Math.round(balance) }];
  for (let k = 0; k <= (payment ? 120 : HORIZON_MONTHS) && balance > 0; k++) {
    const y = today.getUTCFullYear() + Math.floor((today.getUTCMonth() + k) / 12);
    const m = (today.getUTCMonth() + k) % 12;
    if (!months.includes(m + 1)) continue;
    const date = iso(bankDay(dayIn(y, m, sc.on ?? 'last')));
    if (date < TODAY) continue;
    if (sc.until && date > sc.until) break;
    const interest = balance * rate;
    balance = Math.max(0, balance + interest - Math.min(payment, balance + interest));
    plan.push({ date, balance: Math.round(balance) });
  }
  return { plan, debtFree: balance <= 0 ? plan[plan.length - 1].date : null };
}

function recurring(p) {
  const sc = p.script;
  const kind = sc.kind || 'invoice';
  const months = periodMonths(sc);
  const rows = historyRows(p);
  const paidNear = (date) => rows.some((r) => Math.abs(days(r.date, date)) <= 12 && !/interest|ränta/i.test(r.what));
  // Marked done in the glass: a history row that names the point's date ("Done in the glass: Due 2026-11-30").
  const markedFor = (date) => p.history.rows.some((r) => r.some((c) => /done in the glass/i.test(c) && c.includes(date)));
  const today = new Date(`${TODAY}T00:00:00Z`);
  const points = [];
  let balance = Number(sc.balance) || 0;
  // The rate for one period: a monthly invoice carries a twelfth, a quarterly credit a quarter.
  const monthlyRate = (Number(sc.rate) || 0) / 100 / months.length;
  let interestYear = 0;

  // Income is laid out from its first date, so the months that never came are kept (at most a year back).
  const since = kind === 'income' && sc.since ? new Date(`${sc.since}T00:00:00Z`) : null;
  const kStart = since ? Math.max(-12, (since.getUTCFullYear() - today.getUTCFullYear()) * 12 + since.getUTCMonth() - today.getUTCMonth()) : 0;
  // An amount that changes from a date (a lodger who goes back to renting one room): the last change on or before the point.
  const amountAt = (d) => { let a = Number(sc.amount) || null; for (const c of sc.changes || []) if (String(c.from) <= d) a = Number(c.amount) || a; return a; };
  for (let k = kStart; k <= HORIZON_MONTHS; k++) {
    const y = today.getUTCFullYear() + Math.floor((today.getUTCMonth() + k) / 12);
    const m = (((today.getUTCMonth() + k) % 12) + 12) % 12;
    if (!months.includes(m + 1)) continue;
    // Income is not moved to a bank day: the lodger owes it on the day the contract says.
    const due = kind === 'income' ? dayIn(y, m, sc.on ?? 'last') : bankDay(dayIn(y, m, sc.on ?? 'last'));
    if (sc.until && iso(due) > sc.until) break;
    const dueIso = iso(due);
    if (since && dueIso < sc.since) continue;
    const past = dueIso < TODAY;
    const unseen = kind === 'income' && sc.checked && dueIso <= sc.checked ? 'missed' : 'unconfirmed';
    const status = markedFor(dueIso) ? 'done' : past ? (paidNear(dueIso) ? 'done' : unseen) : 'open';
    let amount = amountAt(dueIso);

    if (kind === 'income') {
      points.push({ date: dueIso, name: 'Expected', status, amount, account: sc.account || null });
    } else if (kind === 'credit') {
      const interest = balance * monthlyRate;
      if (!past) interestYear += interest;
      const pay = Math.min(Number(sc.payment) || Number(sc.amount) || 0, balance + interest);
      amount = pay || null;
      if (!past) balance = Math.max(0, balance + interest - pay);
      const arrives = sc.arrives ? dayIn(y, m, sc.arrives) : null;
      if (arrives) points.push({ date: iso(arrives), name: 'Invoice', status: iso(arrives) < TODAY ? 'done' : 'open', amount: null });
      // A credit nobody pays down (a company overdraft) only has its interest added to the debt.
      points.push({ date: dueIso, name: pay ? 'Due' : 'Interest added', status, amount, interest: Math.round(interest), balance: Math.round(balance) });
    } else if (kind === 'draw' || kind === 'card') {
      // A card charge needs no money on an account the day before; a draw does.
      const before = utc(due.getUTCFullYear(), due.getUTCMonth(), due.getUTCDate() - 1);
      if (!past && kind === 'draw') points.push({ date: iso(before), name: `${amount ? kr(amount) : 'The amount'} on ${sc.account || 'the account'}`, status: 'open', amount, account: sc.account || null });
      points.push({ date: dueIso, name: kind === 'card' ? 'Charged' : 'Drawn', status, amount, account: sc.account || null });
    } else {
      if (sc.arrives) {
        const a = Number(sc.arrives) > (sc.on === 'last' ? 31 : Number(sc.on)) ? dayIn(y, m - 1, sc.arrives) : dayIn(y, m, sc.arrives);
        points.push({ date: iso(a), name: 'Invoice arrives', status: iso(a) < TODAY ? 'done' : 'open', amount });
      }
      points.push({ date: dueIso, name: 'Due', status, amount, account: sc.account || null });
    }
  }
  // Fixed dates the script names: a renewal, a credit that runs out, a price change.
  for (const e of sc.dates || []) points.push({ date: e.date, name: e.name, status: e.date < TODAY ? 'done' : 'open', amount: e.amount ?? null, deadline: true });
  points.sort((a, b) => a.date.localeCompare(b.date));

  // Income: everything that came in since the first date pays the oldest month first. A point marked
  // done in the glass counts as paid without using any money. What is still missing up to `checked` is `owed`.
  let owed = null;
  if (kind === 'income') {
    const from = since ? iso(utc(since.getUTCFullYear(), since.getUTCMonth(), since.getUTCDate() - 12)) : null;
    let paid = rows.filter((r) => (!from || r.date >= from) && r.amount > 0).reduce((s, r) => s + r.amount, 0);
    owed = 0;
    for (const x of points.filter((x) => x.name === 'Expected')) {
      if (markedFor(x.date)) { x.status = 'done'; continue; }
      const need = x.amount || 0;
      const cover = Math.min(paid, need);
      paid -= cover;
      if (cover > 0 && cover < need) x.paid = cover;
      if (cover >= need) { x.status = 'done'; continue; }
      if (x.date >= TODAY) { x.status = 'open'; continue; }
      x.status = sc.checked && x.date <= sc.checked ? 'missed' : 'unconfirmed';
      x.owed = need - cover;
      if (x.status === 'missed') owed += x.owed;
    }
    if (paid > 0) owed -= paid; // paid ahead: a negative sum
  }

  const next = points.find((x) => x.date >= TODAY && x.status !== 'done' && /due|drawn|charged|interest|expected/i.test(x.name)) || points.find((x) => x.date >= TODAY && x.status !== 'done');
  return {
    kind, every: sc.every || 'month', amount: Number(sc.amount) || null, account: sc.account || null,
    pay: sc.pay || null, priority: sc.priority ?? null,
    balance: sc.balance != null ? Number(sc.balance) : null, rate: sc.rate != null ? Number(sc.rate) : null,
    interestYear: kind === 'credit' ? Math.round(interestYear) : null,
    ...(kind === 'credit' && creditPlan(sc, months)),
    owed: kind === 'income' ? Math.round(owed) : null,
    next: next || null, points, history: rows.filter((r) => days(r.date, TODAY) <= 366),
  };
}

// ── Daily routines: the morning, a check of mood and energy ─────────────
// A thread whose script says `every: 'day'` (or 'day 07:00') is a routine: a point every day.
// The history has a row per day, `| Date | Status | <one column per measure> | Note |`; a day that
// passed without a row is written as `skipped` once, with no reminder.
// `measure: { mood: [1, 5], energy: [1, 5] }` names the values the history holds per day;
// the runner reads them and works out how often the routine was done and how the values swing, so
// the glass only draws. Health data: only in a private Heim.
const ROUTINE = /^day(?:\s+(\d{1,2}:\d{2}))?$/;
const ROUTINE_BACK_DAYS = 90;
const ROUTINE_AHEAD_DAYS = 7;
const ROUTINE_CATCH_UP_DAYS = 60;
const addDays = (isoDate, n) => iso(new Date(Date.parse(`${isoDate}T00:00:00Z`) + n * 86400000));

function routineRows(p, measure) {
  const h = p.history.header;
  const iDate = h.findIndex((x) => /date/i.test(x));
  const iStatus = h.findIndex((x) => /status/i.test(x));
  const iNote = h.findIndex((x) => /note/i.test(x));
  const cols = Object.keys(measure).map((k) => [k, h.findIndex((x) => x.trim().toLowerCase() === k.toLowerCase())]);
  const byDate = new Map();
  for (const r of p.history.rows) {
    const date = (r[iDate] || '').match(DATE)?.[1];
    if (!date) continue;
    const status = /done/i.test(r[iStatus] || '') ? 'done' : /skip|missed/i.test(r[iStatus] || '') ? 'skipped' : 'done';
    const values = {};
    for (const [k, i] of cols) {
      const n = Number(String(r[i] ?? '').replace(',', '.'));
      if (i >= 0 && r[i] !== '' && Number.isFinite(n)) values[k] = n;
    }
    // A later row for the same day wins: "done" from the glass after a "skipped" from the runner.
    const prev = byDate.get(date);
    if (!prev || status === 'done' || prev.status !== 'done')
      byDate.set(date, { date, status, values, note: iNote >= 0 ? r[iNote] || '' : '' });
  }
  return byDate;
}

function routine(p) {
  const sc = p.script;
  const measure = sc.measure && typeof sc.measure === 'object' ? sc.measure : {};
  const time = String(sc.every).match(ROUTINE)?.[1] || null;
  const rows = routineRows(p, measure);
  const dates = [...rows.keys()].sort();
  // The routine starts on its first history row, or `since`, or today.
  const start = [sc.since, dates[0], TODAY].filter(Boolean).sort()[0];

  // The days that passed without a row become `skipped`, written once into the history.
  const missed = [];
  const from = [start, addDays(TODAY, -ROUTINE_CATCH_UP_DAYS)].sort()[1];
  for (let d = from; d < TODAY; d = addDays(d, 1)) if (!rows.has(d)) missed.push(d);

  const points = [];
  for (let d = [start, addDays(TODAY, -ROUTINE_BACK_DAYS)].sort()[1]; d < TODAY; d = addDays(d, 1)) {
    const r = rows.get(d);
    points.push({ date: d, name: 'Day', status: r ? r.status : 'skipped', values: r?.values || {}, ...(r?.note && { note: r.note }) });
  }
  for (let k = 0; k < ROUTINE_AHEAD_DAYS; k++) {
    const d = addDays(TODAY, k);
    const r = rows.get(d);
    points.push({ date: d, name: 'Day', status: r?.status === 'done' ? 'done' : 'open', values: r?.values || {} });
  }

  // How often it was done, and the values on average, the last 7 and 30 days (counted from the start).
  // Today counts once it is done; until then it is still open, not a missed day.
  const counted = (x) => x.date < TODAY || (x.date === TODAY && x.status === 'done');
  const window = (n) => points.filter((x) => counted(x) && x.date > addDays(TODAY, -n));
  const stat = (n) => {
    const w = window(n);
    const done = w.filter((x) => x.status === 'done');
    const avg = {};
    for (const k of Object.keys(measure)) {
      const v = done.map((x) => x.values[k]).filter((x) => x != null);
      avg[k] = v.length ? Math.round((v.reduce((a, b) => a + b, 0) / v.length) * 10) / 10 : null;
    }
    return { days: w.length, done: done.length, avg };
  };
  const today = points.find((x) => x.date === TODAY);
  return {
    kind: 'routine', every: String(sc.every), time, measure,
    next: today && today.status !== 'done' ? today : points.find((x) => x.date > TODAY) || null,
    points, missed,
    stats: { week: stat(7), month: stat(30) },
    history: [],
  };
}

/** The history rows for the missed days, fitted to the table's own columns. */
function skippedRows(p, days) {
  const h = p.history.header;
  return days.map((d) => `| ${h.map((x) => (/date/i.test(x) ? d : /status/i.test(x) ? 'skipped' : '')).join(' | ')} |`);
}

// ── Updating one process ────────────────────────────────────────────────
/** What the runner cannot do must show as a script error, never run as something else ('day' is not a month). */
function checkScript(sc) {
  if (sc._error) return sc;
  const kinds = ['invoice', 'draw', 'card', 'credit', 'income'];
  if (sc.every != null && !/^(month|quarter|year|\d+ months?)$/.test(String(sc.every)) && !ROUTINE.test(String(sc.every)))
    return { ...sc, _error: `every: '${sc.every}' is not something the runner can do ('day', 'day HH:MM', 'month', 'quarter', 'year' or 'N months')` };
  if (sc.measure != null && (typeof sc.measure !== 'object' || Object.values(sc.measure).some((r) => !Array.isArray(r) || r.length !== 2 || r.some((n) => typeof n !== 'number'))))
    return { ...sc, _error: "measure: each value is a range, e.g. { mood: [1, 5] }" };
  if (sc.kind != null && !kinds.includes(sc.kind)) return { ...sc, _error: `kind: '${sc.kind}' is not one of ${kinds.join(', ')}` };
  for (const k of ['due', 'until', 'since', 'checked']) if (sc[k] != null && !/^\d{4}-\d{2}-\d{2}$/.test(String(sc[k]))) return { ...sc, _error: `${k}: '${sc[k]}' is not a date (YYYY-MM-DD)` };
  return sc;
}

function evaluate(p, doneIds) {
  p = { ...p, script: checkScript(p.script) };
  if (!p.script._error && ROUTINE.test(String(p.script.every ?? ''))) {
    const id = path.relative(TASKS, p.file).replace(/\\/g, '/').replace(/\.md$/, '');
    const r = routine(p);
    let text = p.text;
    const consequences = [];
    if (r.missed.length) {
      const add = skippedRows(p, r.missed);
      text = text.replace(/(## History\r?\n(?:.*\r?\n)*?\|[-| ]+\|\r?\n(?:\|.*\|\r?\n)*)/, (blk) => blk + add.join('\n') + '\n');
      // A routine's missed day is skipped quietly, unless its script asks for a warning.
      const api = { warn: (m) => consequences.push(m), skip: () => {} };
      if (typeof p.script.onMissed === 'function') { try { p.script.onMissed(api); } catch {} }
    }
    const { missed, ...rest } = r;
    const due = r.next?.date || null;
    const status = r.next?.date === TODAY ? 'upcoming' : 'open';
    // Sub-threads: the days done, the days in the log, and today.
    const sub = runsOf(p, [...r.points.filter((x) => x.status === 'done').map((x) => x.date), TODAY]);
    return { id, title: p.title, field: p.field, owner: p.owner, due, status, blockedBy: null, then: null,
             consequences, error: null, changed: text !== p.text, text, ...rest, ...(sub && { sub }) };
  }
  if (p.script.every) {
    const id = path.relative(TASKS, p.file).replace(/\\/g, '/').replace(/\.md$/, '');
    // A script the runner cannot read lays out no points: wrong points are worse than none.
    const r = p.script._error ? { kind: p.script.kind || null, points: [], history: [], next: null } : recurring(p);
    const prepareDays = parseInt(String(p.script.prepare || '7'), 10) || 7;
    const due = r.next?.date || null;
    // An income that never came is a consequence, shown until it is paid or marked done.
    const consequences = r.kind === 'income' && r.owed > 0 ? [`${kr(r.owed)} has not come in (${r.points.filter((x) => x.status === 'missed').map((x) => `${kr(x.owed)} expected ${x.date}`).join(', ')})`] : [];
    const status = p.script._error ? 'script-error' : consequences.length ? 'consequence' : due && days(TODAY, due) <= prepareDays ? 'upcoming' : 'open';
    const invoices = invoicesOf(p);
    return { id, title: p.title, field: p.field, owner: p.owner, due, status, blockedBy: null, then: null,
             consequences, error: p.script._error || null, changed: false, text: p.text, ...r,
             ...(invoices.length && { invoices }) };
  }
  const id = path.relative(TASKS, p.file).replace(/\\/g, '/').replace(/\.md$/, '');
  const sc = p.script;
  const consequences = []; const newHistory = []; let text = p.text;
  const iStatus = p.points.header.findIndex((h) => /status/i.test(h));
  const iWhen = p.points.header.findIndex((h) => /when/i.test(h));
  const open = p.points.rows.filter((r) => /^\s*open\b/i.test(r[iStatus] || ''));
  const blockedBy = sc.after && !doneIds.has(sc.after) ? sc.after : null;
  const has = (what) => p.history.rows.some((r) => r.some((c) => c.includes(what)));

  // A point whose date has passed while it is open becomes missed, once (a history row is written).
  // A missed point stays a standing consequence on every run until someone deals with it.
  const late = p.points.rows.filter((r) => /^\s*(open|missed)\b/i.test(r[iStatus] || ''));
  for (const r of late) {
    const d = (r[iWhen] || '').match(DATE)?.[1];
    if (!d || TODAY <= d) continue;
    const what = `Missed: ${r[0]} (${d})`;
    const api = { warn: (m) => consequences.push(m), skip: () => consequences.push(`${r[0]} skipped`) };
    const before = consequences.length;
    if (typeof sc.onMissed === 'function') { try { sc.onMissed(api); } catch {} }
    if (consequences.length === before) consequences.push(`${r[0]} missed`);
    if (!has(what)) newHistory.push(`| ${TODAY} | ${what} | ${consequences.at(-1)} · by the ${BY} |`);
    if (/^\s*open\b/i.test(r[iStatus] || '')) {
      const oldRow = `| ${r.join(' | ')} |`;
      const newRow = `| ${r.map((c, i) => (i === iStatus ? 'missed' : c)).join(' | ')} |`;
      text = text.replace(oldRow, newRow);
    }
  }
  if (newHistory.length) {
    text = text.replace(/(## History\r?\n(?:.*\r?\n)*?\|[-| ]+\|\r?\n(?:\|.*\|\r?\n)*)/, (blk) => blk + newHistory.join('\n') + '\n');
  }
  const prepareDays = parseInt(String(sc.prepare || '0'), 10) || 0;
  const due = sc.due || null;
  const status = sc._error ? 'script-error'
    : consequences.length ? 'consequence'
    : open.length === 0 ? 'done'
    : due && TODAY > due ? 'overdue'
    : blockedBy ? 'blocked'
    : due && days(TODAY, due) <= prepareDays ? 'upcoming'
    : 'open';
  // The process's own points, as the file has them after this run, so the glass can show and mark each.
  const pts = sections(text).points;
  const t = table(pts);
  const iS = t.header.findIndex((h) => /status/i.test(h));
  const iW = t.header.findIndex((h) => /when/i.test(h));
  const points = t.rows.map((r) => ({ name: r[0], when: iW >= 0 ? r[iW] || '' : '', date: (iW >= 0 && (r[iW] || '').match(DATE)?.[1]) || null, status: (iS >= 0 && r[iS]) || 'open' }));
  const sub = runsOf(p, null);
  return { id, title: p.title, field: p.field, owner: p.owner, due, status, blockedBy,
           then: sc.then || null, consequences, error: sc._error || null, points, changed: text !== p.text, text, ...(sub && { sub }) };
}

// ── The whole Heim ──────────────────────────────────────────────────────
function walk(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
    const f = path.join(dir, e.name);
    if (e.isDirectory()) return walk(f);
    return e.name.endsWith('.md') && !['inbox.md', 'field.md'].includes(e.name) ? [f] : [];
  });
}
const procs = walk(TASKS).map(readProcess).filter((p) => p.script && Object.keys(p.script).length);
const idOf = (p) => path.relative(TASKS, p.file).replace(/\\/g, '/').replace(/\.md$/, '');
const doneIds = new Set(procs.filter((p) => {
  const iS = p.points.header.findIndex((h) => /status/i.test(h));
  return p.points.rows.length && p.points.rows.every((r) => /done|skipped/i.test(r[iS] || ''));
}).map(idOf));
const results = procs.map((p) => evaluate(p, doneIds));

const heimDir = path.join(ROOT, PLAN.machine);
const warnings = results.filter((r) => r.consequences.length).map((r) => ({ process: r.id, text: r.consequences.join('; ') }));
const hasLighthouse = PLAN.lighthouse;
const lhFile = path.join(heimDir, 'lighthouse.json');
let lighthouse = null;
if (fs.existsSync(lhFile)) { try { lighthouse = JSON.parse(fs.readFileSync(lhFile, 'utf8')); } catch {} }
if (BY === 'watchdog' && hasLighthouse) {
  const age = lighthouse?.last ? (Date.now() - Date.parse(lighthouse.last)) / 3600000 : Infinity;
  if (age > LIGHTHOUSE_MAX_HOURS) warnings.push({ process: null, notify: true, title: 'The agents are asleep',
    text: (lighthouse?.last ? `The lighthouse has been dark since ${lighthouse.last.slice(0, 16).replace('T', ' ')} UTC.` : 'The lighthouse has not reported yet.') + ' Nothing is lost: the Watchdog keeps the house running and the glass current until the agents wake.' });
}

// What must be on each account, the next 45 days: every draw and due date with its amount.
const cash = {};
for (const r of results) {
  for (const pt of r.points || []) {
    if (!/^(drawn|due)$/i.test(pt.name) || pt.status === 'done' || pt.date < TODAY || days(TODAY, pt.date) > 45 || !pt.amount) continue;
    const acc = r.account || 'Not set';
    (cash[acc] ||= { total: 0, items: [] }).items.push({ date: pt.date, process: r.id, title: r.title, amount: pt.amount, kind: r.kind });
    cash[acc].total += pt.amount;
  }
}
for (const c of Object.values(cash)) { c.items.sort((a, b) => a.date.localeCompare(b.date)); c.total = Math.round(c.total); }

const timeline = { updated: new Date().toISOString(), today: TODAY, by: BY, warnings, cash,
  processes: results.map(({ text, changed, ...r }) => r) };

// A nested Heim without processes (only `- [ ]` lines in its tasks folder) gets no timeline of its own.
if (!DRY && !(args.includes('--nested') && !results.length)) {
  for (const r of results) if (r.changed) fs.writeFileSync(path.join(TASKS, r.id + '.md'), r.text, 'utf8');
  fs.mkdirSync(heimDir, { recursive: true });
  // Rewrite the timeline only when something besides the timestamp changed, so git stays quiet.
  const tlFile = path.join(heimDir, 'timeline.json');
  const strip = ({ updated, by, ...rest }) => JSON.stringify(rest);
  let prev = null; try { prev = JSON.parse(fs.readFileSync(tlFile, 'utf8')); } catch {}
  if (!prev || strip(prev) !== strip(timeline)) fs.writeFileSync(tlFile, JSON.stringify(timeline, null, 2) + '\n', 'utf8');
  // The heartbeat is the outer Heim's: a nested run never writes one.
  if (BY === 'lighthouse' && !args.includes('--nested')) fs.writeFileSync(lhFile, JSON.stringify({ last: new Date().toISOString() }, null, 2) + '\n', 'utf8');
  // What the Watchdog should tell the owner: one stable title per line, so a warning is raised once.
  fs.writeFileSync(path.join(ROOT, PLAN.notify), warnings.filter((w) => w.notify).map((w) => `${w.title || w.text}\t${w.text}`).join('\n'), 'utf8');
}

// ── The Heims inside this one ───────────────────────────────────────────
// A folder below with its own floor plan and processes folder is a Heim of its own (every heimai.yaml
// or heim.yaml, at any depth): a project whose orders are a timeline of their own. The runner runs it
// the same way, writing its own timeline, so the Watchdog and the rounds keep every project current
// without being told about it. A `heimai.yaml` in a folder named `.heimai` belongs to the folder above.
const SKIP = new Set(['node_modules', 'agents', 'tasks', 'machine']);
function nestedRoots(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
    if (!e.isDirectory() || SKIP.has(e.name) || (e.name.startsWith('.') && e.name !== '.heimai')) return [];
    const f = path.join(dir, e.name);
    const roots = [];
    if (fs.existsSync(path.join(f, 'heimai.yaml'))) roots.push(e.name === '.heimai' ? dir : f);
    else if (fs.existsSync(path.join(f, 'heim.yaml'))) roots.push(f);
    const here = roots.filter((r) => path.resolve(r) !== ROOT && fs.existsSync(path.join(r, planOf(r).tasksDir)));
    return [...here, ...nestedRoots(f)];
  });
}
if (!args.includes('--nested')) {
  const { execFileSync } = await import('node:child_process');
  const { fileURLToPath } = await import('node:url');
  for (const root of [...new Set(nestedRoots(ROOT).map((r) => path.resolve(r)))]) {
    console.log(`\n── ${path.relative(ROOT, root).replace(/\\/g, '/')} ──`);
    const pass = ['--root', root, '--by', BY, '--today', TODAY, '--nested', ...(DRY ? ['--dry'] : [])];
    console.log(execFileSync(process.execPath, [fileURLToPath(import.meta.url), ...pass], { encoding: 'utf8' }).trimEnd());
  }
}

for (const r of results) console.log(`${r.status.padEnd(12)} ${r.id}${r.due ? '  due ' + r.due : ''}${r.blockedBy ? '  after ' + r.blockedBy : ''}${r.consequences.length ? '  → ' + r.consequences.join('; ') : ''}${r.error ? '  → ' + r.error : ''}${r.changed ? '  (file updated)' : ''}`);
for (const w of warnings.filter((w) => !w.process)) console.log(`WARNING      ${w.text}`);
console.log(`${results.length} processes · ${warnings.length} warnings · ${TODAY} · by the ${BY}${DRY ? ' · dry run' : ''}`);
