// Run state, settings and translations.
const store = {
  get(k, d) { try { const v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); } catch { return d; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* private mode */ } },
};

export const START_DEBT = 700000;
export const WAGE = 12400;

export const S = {
  lang: store.get("oms.lang", (navigator.language || "en").toLowerCase().startsWith("ko") ? "ko" : "en"),
  muted: store.get("oms.muted", false),
  best: store.get("oms.best", 0),
  runs: store.get("oms.runs", 0),
  seen: store.get("oms.seen", {}),     // rules whose first-time hint the player has survived
  run: null,
};

export function markSeen(keys) { keys.forEach(k => { S.seen[k] = true; }); store.set("oms.seen", S.seen); }

/** Continuing after a death costs a cleanup fee added to the debt. Twice per run at most. */
export const MAX_CONTINUES = 2;
export const continueCost = n => 100000 * (n + 1);

export function saveSettings() { store.set("oms.lang", S.lang); store.set("oms.muted", S.muted); }

export function newRun() {
  S.runs += 1; store.set("oms.runs", S.runs);
  S.run = { shift: 1, earned: 0, debt: START_DEBT, cleared: 0, continues: 0 };
  return S.run;
}

export function recordBest() {
  if (S.run && S.run.cleared > S.best) { S.best = S.run.cleared; store.set("oms.best", S.best); }
}

// Rules stack up: door (1), 03:33 (2), the Regular (3), the Regular in disguise (4), the fridge (5+).
export const RULES = ["door", "clock", "regular", "regular", "fridge"];
export function rulesFor(shift) { return [...new Set(RULES.slice(0, Math.min(shift, RULES.length)))]; }
/** What the manager hands you on the job card for this shift. */
export function newRuleFor(shift) { return shift === 4 ? "disguise" : RULES[Math.min(shift, RULES.length) - 1]; }

export function won(n) { return "₩" + Math.max(0, Math.round(n)).toLocaleString("en-US"); }

const STR = {
  ko: {
    start: "아무 키나 누르세요", best: n => `최고 기록 · ${n}번째 교대`, lang: "한국어", loading: "출근 준비 중",
    rule_door: "그것이 오면 문을 바라보시오", rule_clock: "03:33에는 움직이지 마시오", rule_regular: "단골은 계산해 주지 마시오", rule_fridge: "03:40 이후 냉장고를 열지 마시오", rule_disguise: "그림자 없는 손님은 단골이다",
    rule: "규칙", rulePre: "규칙: ", place: "달빛마트 야간", wageLine: "₩12,400 + 수당",
    shiftN: n => `${n}번째 교대`, go: "출근", next: "▼",
    intro: ["어서 와. 일은 간단해.", "손님 계산하고, 물건 채우고.", "일당은 넉넉해. 규칙은 딱 하나."],
    again: ["...또 왔어?", "좋아. 한 번만 더."],
    more: ["살아서 퇴근했네. 수고했어.", "오늘은 규칙이 하나 늘었어."],
    same: ["아직 빚이 남았지?", "규칙은 그대로야. 잊지 마."],
    brief4: ["단골 말인데... 요즘 얼굴을 바꿔.", "그림자 없는 손님은 계산하지 마."],
    brief5: ["냉장고는 03:40까지만 열어.", "그 뒤엔 돈을 세 배 준대도 열지 마."],
    cont: ["...살아 있네?", "청소비는 빚에 얹어 둘게."],
    hint_clock: "03:33엔 그대로 멈춰!", hint_regular: "▼ 단골 · 계산 금지", hint_fridge: "03:40부터 열지 마!", hint_disguise: "그림자가 없다...",
    cont_btn: "이어하기", cont_cost: c => `이어하기 비용 ${c}`, x3: "x3",
    hint: "이동: 방향키·터치   작업: Space·터치   문 보기: ↑·문 터치",
    quotaLine: q => `오늘 목표 ${q}`, lookHint: "▲ 문을 보세요!",
    serve: "계산", restock: "진열", pickup: "줍기",
    strike: "손님 불만!", clockout: "퇴근 성공", bonus: "완주 수당",
    cause_door: "문에서 눈을 뗐다", cause_quota: "목표 미달", cause_clock: "03:33에 움직였다", cause_regular: "단골을 계산해 줬다", cause_fridge: "냉장고를 열었다",
    cause_fired: "손님 불만 3회", cause_win: "없음 · 빚 청산",
    over_fail: "퇴근 실패", over_fired: "해고", over_win: "빚 청산!",
    retry: "다시", share: "공유", saved: "저장됨!", debt: "남은 빚",
    survived: n => `${n}번 퇴근`, shiftRow: n => `${n}번째 교대`,
    shareText: (n, cause) => `한 번만 더: ${n}번째 교대에서 끝. 사인 — ${cause}`,
  },
  en: {
    start: "PRESS ANY KEY", best: n => `BEST · SHIFT ${n}`, lang: "ENGLISH", loading: "Clocking in",
    rule_door: "When it comes, face the door", rule_clock: "Do not move at 03:33", rule_regular: "Never ring up the Regular", rule_fridge: "Don't open the fridge after 03:40", rule_disguise: "No shadow? It's the Regular",
    rule: "RULE", rulePre: "", place: "Dalbit Mart", wageLine: "₩12,400 +",
    shiftN: n => `SHIFT ${n}`, go: "CLOCK IN", next: "▼",
    intro: ["Come in. The job is simple.", "Ring up customers. Stock shelves.", "Pay is generous. One rule only."],
    again: ["...Back again?", "Fine. One more shift."],
    more: ["You clocked out alive. Good work.", "Tonight there is one more rule."],
    same: ["Still in debt, aren't you?", "Same rules. Don't forget them."],
    brief4: ["About the Regular... it wears other faces now.", "No shadow? Don't ring them up."],
    brief5: ["The fridge closes at 03:40.", "Even if it pays triple. Don't open it."],
    cont: ["...You're alive?", "The cleanup fee goes on your tab."],
    hint_clock: "FREEZE at 03:33!", hint_regular: "▼ THE REGULAR · DON'T SERVE", hint_fridge: "NOT AFTER 03:40!", hint_disguise: "No shadow...",
    cont_btn: "CONTINUE", cont_cost: c => `Continue costs ${c}`, x3: "x3",
    hint: "Move: arrows/tap  Work: Space/tap  Look: ↑ or tap door",
    quotaLine: q => `Tonight's quota ${q}`, lookHint: "▲ LOOK AT IT!",
    serve: "RING UP", restock: "RESTOCK", pickup: "PICK UP",
    strike: "Complaint!", clockout: "CLOCKED OUT", bonus: "Shift bonus",
    cause_door: "Looked away", cause_quota: "Missed the quota", cause_clock: "Moved at 03:33", cause_regular: "Served the Regular", cause_fridge: "Opened the fridge",
    cause_fired: "3 complaints", cause_win: "None. Debt paid",
    over_fail: "SHIFT FAILED", over_fired: "FIRED", over_win: "DEBT CLEARED!",
    retry: "RETRY", share: "SHARE", saved: "Saved!", debt: "Debt left",
    survived: n => `${n} shifts cleared`, shiftRow: n => `Shift ${n}`,
    shareText: (n, cause) => `ONE MORE SHIFT: ended on shift ${n}. Cause: ${cause}`,
  },
};

export function t(key, ...a) {
  const v = STR[S.lang][key] ?? STR.en[key] ?? key;
  return typeof v === "function" ? v(...a) : v;
}
