// Run state, settings and translations.
const store = {
  get(k, d) { try { const v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); } catch { return d; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* private mode */ } },
};

// Pay matches the show: each gig pays a multiple of the 2026 minimum wage (₩10,320 an hour), taken
// from the show's gig in the same slot: store 50x (episode 1, ₩4M a night), event 75x (episode 2's
// ₩6M a day, scaled by the same rate), delivery 200x (episode 3's milk run), cinema 100x (no figure in
// the show; 100x is what the agency offers after the first job), construction 200x (episode 6).
// A shift is one in-game hour, so a cleared shift pays one hour at that rate.
export const MIN_WAGE = 10320;
export const MULT = { 1: 50, 2: 75, 3: 200, 4: 100, 6: 200 };
export const hourly = act => MIN_WAGE * (MULT[act] || 50);
export const START_DEBT = 20000000;

export const S = {
  lang: store.get("oms.lang", (navigator.language || "en").toLowerCase().startsWith("ko") ? "ko" : "en"),
  muted: store.get("oms.muted", false),
  best: store.get("oms.best", 0),
  runs: store.get("oms.runs", 0),
  seen: store.get("oms.seen", {}),     // rules whose first-time hint the player has survived
  acts: store.get("oms.acts", {}),     // story acts cleared, e.g. { 1: true } once the Rat King is beaten
  run: null,
};

// ---- daily shift: one seeded night for everyone, one attempt per day (local date)
const DAY0 = Date.UTC(2026, 10, 11);
export function today() {
  const d = new Date();
  return Math.floor((Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()) - DAY0) / 86400000) + 1;
}
export function dailyRecord() { const r = store.get("oms.daily", null); return r && r.n === today() ? r : null; }
export function saveDaily(rec) { store.set("oms.daily", { n: today(), ...rec }); }
export function newDailyRun() {
  const n = today();
  S.run = { shift: 4 + (n % 4), earned: 0, debt: START_DEBT, cleared: 0, continues: 0, daily: n };
  saveDaily({ done: false });
  return S.run;
}
/** Small seeded PRNG so every player gets the same night. */
export function seeded(seed) {
  let a = seed >>> 0;
  return () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}

// The job board: one workplace per act, in the order the show's gigs come.
export const ACTS = [
  { n: 1, key: "store", built: true },
  { n: 2, key: "event", built: true },
  { n: 3, key: "delivery", built: true },
  { n: 4, key: "cinema" },
  { n: 5, key: "trial" },
  { n: 6, key: "site" },
  { n: 7, key: "park" },
];
export function clearAct(n, run) {
  S.acts[n] = true; store.set("oms.acts", S.acts);
  // the next job carries this run's money: debt and earnings pick up where this act left off
  if (run) { const c = store.get("oms.career", {}); c[n] = { debt: run.debt, earned: run.earned, cleared: run.cleared }; store.set("oms.career", c); }
}
/** An act is open once the one before it is cleared. */
export const actOpen = n => n === 1 || !!S.acts[n - 1];

export function markSeen(keys) { keys.forEach(k => { S.seen[k] = true; }); store.set("oms.seen", S.seen); }

/** Continuing after a death costs a cleanup fee added to the debt. Twice per run at most. */
export const MAX_CONTINUES = 2;
export const continueCost = n => 500000 * (n + 1);

export function saveSettings() { store.set("oms.lang", S.lang); store.set("oms.muted", S.muted); }

export function newRun(act = 1) {
  S.runs += 1; store.set("oms.runs", S.runs);
  const prev = act > 1 ? store.get("oms.career", {})[act - 1] : null;
  S.run = { shift: 1, earned: prev?.earned || 0, debt: prev?.debt ?? START_DEBT, cleared: prev?.cleared || 0, continues: 0, act };
  return S.run;
}

export function recordBest() {
  if (S.run && S.run.cleared > S.best) { S.best = S.run.cleared; store.set("oms.best", S.best); }
}

// One new rule per shift: the door (1), the stockroom knock (2), 03:33 (3), the Regular (4),
// the streetlamp outside (5), the Regular in disguise (6), the fridge (7).
export const RULES = ["door", "knock", "clock", "regular", "lamp", "regular", "fridge"];
export function rulesFor(shift) { return [...new Set(RULES.slice(0, Math.min(shift, RULES.length)))]; }
/** What the manager hands you on the job card for this shift. */
export function newRuleFor(shift) {
  const g = GIG[S.run?.act];
  if (g?.rules) return g.rules[Math.min(shift, g.rules.length) - 1];
  return shift === 6 ? "disguise" : RULES[Math.min(shift, RULES.length) - 1];
}

// Act 2, the night event: balloons for kids only (1), the mascot's head (2), don't answer it (3).
export const ERULES = ["balloon", "head", "answer"];
export const erulesFor = shift => ERULES.slice(0, Math.min(shift, ERULES.length));
// Act 3, dawn delivery: floor 4 (1), the door that opens first (2), no elevator after 02:00 (3).
export const DRULES = ["floor4", "opendoor", "elevator"];
export const drulesFor = shift => DRULES.slice(0, Math.min(shift, DRULES.length));

/** Per-act setup: which scene runs the shift, the place on the job card, the manager's lines. */
export const GIG = {
  1: { scene: "Shift", place: "place", intro: "intro", briefs: { 2: "brief2", 3: "brief3", 4: "brief4", 5: "brief5", 6: "brief6", 7: "brief7" } },
  2: { scene: "Event", place: "place2", intro: "e_intro", briefs: { 2: "e_brief2", 3: "e_brief3" }, rules: ERULES },
  3: { scene: "Delivery", place: "place3", intro: "d_intro", briefs: { 2: "d_brief2", 3: "d_brief3" }, rules: DRULES },
};

export function won(n) { return "₩" + Math.max(0, Math.round(n)).toLocaleString("en-US"); }

const STR = {
  ko: {
    board: "새벽인력 · 일자리 게시판", act: n => `${n}막`, st_clear: "완료", st_open: "모집 중", st_soon: "준비 중", st_locked: "잠김",
    job_store: "편의점", job_event: "행사", job_delivery: "우유배달", job_cinema: "극장", job_trial: "임상시험", job_site: "공사장", job_park: "놀이공원",
    jd_store: "사흘 밤을 버티고 쥐왕을 쓰러뜨려라", jd_soon: "다음 업데이트에서 문을 엽니다", jd_locked: "앞의 일을 먼저 끝내세요",
    jd_keep: "계속 근무: 편의점 다음 교대", board_clear: "곽 실장: 준호? 모르는 이름인데. 다음 일이나 보자.", act_clear: "1막 완료",
    place3: "해달 오피스텔 배달",
    jd_delivery: "사흘 새벽 우유배달 · 보스는 준비 중", jd_event: "사흘 밤 행사 버티기 · 보스는 준비 중",
    rule_floor4: "4층에는 배달하지 마시오", rule_opendoor: "노크 전에 문이 열리면 돌아서시오", rule_elevator: "02:00 이후 엘리베이터 금지",
    cause_floor4: "4층에 배달했다", cause_opendoor: "먼저 열린 문 앞에 남았다", cause_elevator: "엘리베이터를 탔다", cause_wrong: "엉뚱한 집 노크",
    d_intro: ["새벽 우유배달이야. 오토바이 타지?", "해달 오피스텔로 가.", "주문서 호수 문 앞에 두면 돼.", "아, 4층 주문은 가지 마.", "카운터에 반납해."],
    d_brief2: ["노크 전에 문이 먼저 열리면...", "돌아서. 그 층을 나갔다 다시 와."],
    d_brief3: ["02:00 넘으면 엘리베이터 타지 마.", "...그 주문들, 전부 한 번호였어."],
    order: n => `주문 ${n}호`, noOrder: "주문 없음", dHint: "이동: ←→·터치   행동: Space·↑·터치",
    hint_pick: "Space: 주문 받기", hint_out: "→ 출발", hint_return: "4층 주문! 카운터에 반납", hint_f4: "4층... 노크 금지", hint_open: "문이 먼저 열렸다! 이 층을 떠나!",
    hint_elev: "02:00 이후 계단만", hint_back: "← 1층 아래로 나가 허브로", returned: "반납", wrongFlat: "엉뚱한 집!", tip: "팁",
    stairsUp: "▲", stairsDown: "▼", exitOut: "◀ 밖으로", toHall: "복도",
    place2: "그랜드 오픈 행사", banner: "그랜드 오픈",
    rule_balloon: "풍선은 아이에게만 주시오", rule_head: "탈 머리가 벗겨지면 무대를 보지 마시오", rule_answer: "탈이 이름을 부르면 대답하지 마시오",
    cause_balloon: "어른에게 풍선을 줬다", cause_head: "탈 속을 봤다", cause_answer: "이름에 대답했다",
    e_intro: ["오늘은 행사야. 인형탈 매니저.", "아이들한테 풍선 나눠 주고,", "탈이 더워하면 부채질해 줘.", "어른이 풍선 달라면... 주지 마."],
    e_brief2: ["탈 머리가 벗겨지면...", "무대 보지 마. 돌아서서 기다려."],
    e_brief3: ["탈이 네 이름을 부르면 대답하지 마.", "...걔가 네 이름을 어떻게 알지?"],
    hint_take: "Space: 풍선 들기", hint_give: "아이에게 풍선 (Space)", hint_adult: "어른! 거절하기 (Space)", hint_fan: "부채질 (Space)", hint_turn: "돌아서! →", hint_quiet: "대답 금지! 아무것도 하지 마",
    call: "소라야~", refused: "거절", adultAsk: "풍선 줘", holdBalloon: "풍선 들고 있음", emptyHand: "빈손",
    board_keys: "←→ 고르기 · Space 선택 · Esc 처음으로",
    start: "아무 키나 누르세요", best: n => `최고 기록 · ${n}번째 교대`, lang: "한국어", loading: "출근 준비 중",
    rule_door: "그것이 오면 문을 바라보시오", rule_clock: "03:33에는 움직이지 마시오", rule_regular: "단골은 계산해 주지 마시오", rule_fridge: "03:40 이후 냉장고를 열지 마시오", rule_knock: "철문이 두드리면 창고에서 나가시오", rule_lamp: "가로등 아래 그것을 쳐다보지 마시오", rule_disguise: "그림자 없는 손님은 단골이다",
    rule: "규칙", rulePre: "규칙: ", place: "달빛마트 야간", wageLine: (m, w) => `${m}배 · ${Math.round(w / 10000)}만 원`, wagePaid: "시급",
    shiftN: n => `${n}번째 교대`, go: "출근", next: "▼",
    intro: ["어서 와. 일은 간단해.", "손님 계산하고, 물건 채우고.", "일당은 넉넉해. 규칙은 딱 하나."],
    again: ["...또 왔어?", "좋아. 한 번만 더."],
    more: ["살아서 퇴근했네. 수고했어.", "오늘은 규칙이 하나 늘었어."],
    same: ["아직 빚이 남았지?", "규칙은 그대로야. 잊지 마."],
    brief2: ["상자는 계산대 뒤 창고에 있어.", "철문이 두드리면... 바로 나와."],
    brief3: ["03:33엔 아무것도 하지 마.", "그리고... 덕구, 오늘 좀 이상하지 않았어?"],
    brief4: ["덕구? 우리 가게에 그런 직원은 없어.", "...아무튼 오늘은 '단골'이 와. 계산해 주지 마."],
    brief5: ["쓰레기는 가게 앞에 내놔.", "가로등 밑에 누가 있으면... 보지 마."],
    brief6: ["단골 말인데... 요즘 얼굴을 바꿔.", "그림자 없는 손님은 계산하지 마."],
    brief7: ["냉장고는 03:40까지만 열어.", "그 뒤엔 돈을 세 배 준대도 열지 마."],
    hint_box: "상자 줍기 (Space)", hint_trash: "쓰레기 → 가게 앞 쓰레기통", hint_bins: "쓰레기통에 버리기", hint_knock: "철문 노크! 빨리 나가!", hint_lamp: "왼쪽을 보지 마!",
    toFloor: "▼ 매장", toStore: "▲ 가게로", waiting: n => `손님 ${n}명 대기`,
    dg1: ["새로 왔어? 난 덕구. 같이 야간이야.", "규칙만 지키면 돼. 진짜로.", "나? 여기서 오래 일했지.", "...언제부터였더라."],
    dg2: ["창고 철문은 대답하지 마.", "두드리면 그냥 나와. 상자는 두고.", "네 오빠도 야간 했었지.", "...아, 아무것도 아냐.", "요즘 창고에 쥐가 많아."],
    dg3: ["...배고프다.", "손님들 다 맛있어 보이네.", "킥... 킥킥킥.", "너도."],
    clue1: "계산대 위 타임카드: '준호 · 퇴근 기록 없음'", clue3: "모자 안쪽 명찰: 준호", dgTurn: "이제 그만 참을래.", dgGone: "...", ratking: "쥐왕", rule_boss: "쥐왕을 쓰러뜨리고 살아남으시오",
    cause_ratking: "쥐왕에게 당했다", hazard: "위험수당", hint_fight: "Space·터치: 대걸레! 비틀거릴 때만 먹힌다",
    cont: ["...살아 있네?", "청소비는 빚에 얹어 둘게."],
    hint_clock: "03:33엔 그대로 멈춰!", hint_regular: "▼ 단골 · 계산 금지", hint_fridge: "03:40부터 열지 마!", hint_disguise: "그림자가 없다...",
    daily: n => `오늘의 교대 #${n} ▶`, dailyDone: "오늘 교대는 끝났어요. 내일 또!", dailyRow: n => `오늘의 교대 #${n}`,
    dailyIntro: ["오늘 밤은 다들 같은 가게야.", "기회는 한 번. 규칙은 알지?"], cause_daily: "생존 · 퇴근 성공", over_daily: "오늘의 교대 완료",
    dailyShare: (n, ok, pay, cause) => `한 번만 더 · 오늘의 교대 #${n}\n${ok ? "🟩 퇴근 성공" : "🟥 " + cause}  ${pay}`,
    cont_btn: "이어하기", cont_cost: c => `이어하기 비용 ${c}`, x3: "x3",
    hint: "이동: 방향키·터치   작업: Space·터치   문 보기: ↑·문 터치",
    quotaLine: q => `오늘 목표 ${q}`, lookHint: "▲ 문을 보세요!",
    serve: "계산", restock: "진열", pickup: "줍기",
    strike: "손님 불만!", clockout: "퇴근 성공", bonus: "완주 수당",
    cause_door: "문에서 눈을 뗐다", cause_quota: "목표 미달", cause_clock: "03:33에 움직였다", cause_regular: "단골을 계산해 줬다", cause_fridge: "냉장고를 열었다", cause_knock: "철문이 열렸다", cause_lamp: "가로등 쪽을 봤다",
    cause_fired: "손님 불만 3회", cause_win: "없음 · 빚 청산",
    over_fail: "퇴근 실패", over_fired: "해고", over_win: "빚 청산!",
    retry: "다시", share: "공유", saved: "저장됨!", debt: "남은 빚",
    survived: n => `${n}번 퇴근`, shiftRow: n => `${n}번째 교대`,
    shareText: (n, cause) => `한 번만 더: ${n}번째 교대에서 끝. 사인 — ${cause}`,
  },
  en: {
    board: "DAWN STAFFING · JOB BOARD", act: n => `ACT ${n}`, st_clear: "CLEAR", st_open: "HIRING", st_soon: "SOON", st_locked: "LOCKED",
    job_store: "STORE", job_event: "EVENT", job_delivery: "MILK", job_cinema: "CINEMA", job_trial: "TRIAL", job_site: "SITE", job_park: "PARK",
    jd_store: "Survive three nights and beat the Rat King", jd_soon: "Opens in a future update", jd_locked: "Finish the job before it first",
    jd_keep: "Keep working: next shift at the store", board_clear: "Kwak: Junho? Never heard of him. Let's find your next job.", act_clear: "ACT 1 CLEAR",
    place3: "Haedal Milk Run",
    jd_delivery: "Three dawn milk runs · boss coming soon", jd_event: "Work three event nights · boss coming soon",
    rule_floor4: "Never deliver to the 4th floor", rule_opendoor: "Door opens first? Walk away", rule_elevator: "No elevator after 02:00",
    cause_floor4: "Delivered to 4F", cause_opendoor: "Lingered at the door", cause_elevator: "Took the elevator", cause_wrong: "Knocked on the wrong door",
    d_intro: ["Dawn milk run. You can ride?", "Haedal Officetel.", "Leave bags at the flat on the slip.", "4th-floor orders? Don't go.", "Hand those back at the counter."],
    d_brief2: ["If a door opens before you knock...", "Turn around. Come back later."],
    d_brief3: ["After 02:00, stairs only.", "...Every order: the same phone."],
    order: n => `ORDER ${n}`, noOrder: "NO ORDER", dHint: "Move: ←→/tap   Act: Space/↑/tap",
    hint_pick: "Space: take an order", hint_out: "→ Ride", hint_return: "4th floor! Hand it back", hint_f4: "4th floor... don't knock", hint_open: "It opened first! Leave this floor!",
    hint_elev: "Stairs only after 02:00", hint_back: "← Down from floor 1 to ride back", returned: "Returned", wrongFlat: "Wrong flat!", tip: "Tip",
    stairsUp: "▲", stairsDown: "▼", exitOut: "◀ OUT", toHall: "HALL",
    place2: "Grand Opening", banner: "GRAND OPENING",
    rule_balloon: "Balloons for kids only", rule_head: "Head off? Don't look at the stage", rule_answer: "If it calls your name, don't answer",
    cause_balloon: "Balloon to an adult", cause_head: "Saw inside the suit", cause_answer: "Answered its call",
    e_intro: ["Event work tonight. Mascot handler.", "Hand balloons to the kids,", "fan the suit when it gets hot.", "Grown-up wants a balloon? No."],
    e_brief2: ["If the mascot's head comes off...", "Don't look. Turn around and wait."],
    e_brief3: ["If it calls your name, don't answer.", "...How does it know your name?"],
    hint_take: "Space: grab a balloon", hint_give: "Balloon to the kid (Space)", hint_adult: "Adult! Refuse (Space)", hint_fan: "Fan the suit (Space)", hint_turn: "TURN AWAY! →", hint_quiet: "Don't answer! Do nothing",
    call: "Sora~", refused: "Refused", adultAsk: "Balloon?", holdBalloon: "BALLOON", emptyHand: "EMPTY",
    board_keys: "←→ pick · Space choose · Esc title",
    start: "PRESS ANY KEY", best: n => `BEST · SHIFT ${n}`, lang: "ENGLISH", loading: "Clocking in",
    rule_door: "When it comes, face the door", rule_clock: "Do not move at 03:33", rule_regular: "Never ring up the Regular", rule_fridge: "Don't open the fridge after 03:40", rule_knock: "If the steel door knocks, leave the stockroom", rule_lamp: "Don't look at what stands under the streetlamp", rule_disguise: "No shadow? It's the Regular",
    rule: "RULE", rulePre: "", place: "Dalbit Mart", wageLine: (m, w) => `${m}x · ₩${w >= 1e6 ? (w / 1e6).toFixed(2) + "M" : Math.round(w / 1000) + "K"}`, wagePaid: "Wage",
    shiftN: n => `SHIFT ${n}`, go: "CLOCK IN", next: "▼",
    intro: ["Come in. The job is simple.", "Ring up customers. Stock shelves.", "Pay is generous. One rule only."],
    again: ["...Back again?", "Fine. One more shift."],
    more: ["You clocked out alive. Good work.", "Tonight there is one more rule."],
    same: ["Still in debt, aren't you?", "Same rules. Don't forget them."],
    brief2: ["Boxes are in the stockroom behind the till.", "If the steel door knocks... get out."],
    brief3: ["At 03:33, do nothing.", "And... has Deokgu seemed off to you?"],
    brief4: ["Deokgu? We don't have a Deokgu.", "...Anyway. The Regular comes tonight. Don't ring it up."],
    brief5: ["Take the trash out front.", "If someone's under the streetlamp... don't look."],
    brief6: ["About the Regular... it wears other faces now.", "No shadow? Don't ring them up."],
    brief7: ["The fridge closes at 03:40.", "Even if it pays triple. Don't open it."],
    hint_box: "Grab a box (Space)", hint_trash: "Trash → bins out front", hint_bins: "Drop it in the bins", hint_knock: "KNOCKING! GET OUT!", hint_lamp: "Don't look left!",
    toFloor: "▼ SHOP", toStore: "▲ STORE", waiting: n => `${n} waiting`,
    dg1: ["New? I'm Deokgu. Nights too.", "Keep the rules and you're fine. Really.", "Me? Been here a long time.", "...Since when, again?"],
    dg2: ["Don't answer the steel door.", "If it knocks, get out. Leave the box.", "Your brother worked nights too.", "...Forget I said that.", "Lots of rats in the back lately."],
    dg3: ["...I'm hungry.", "The customers look tasty tonight.", "Heh... heh heh heh.", "So do you."],
    clue1: "Time card by the till: 'JUNHO · never clocked out'", clue3: "Name tag inside the cap: JUNHO", dgTurn: "I can't hold it anymore.", dgGone: "...", ratking: "RAT KING", rule_boss: "Beat the Rat King and survive",
    cause_ratking: "Eaten by the Rat King", hazard: "Hazard pay", hint_fight: "Space/tap: swing the mop! Only hurts when it's dazed",
    cont: ["...You're alive?", "The cleanup fee goes on your tab."],
    hint_clock: "FREEZE at 03:33!", hint_regular: "▼ THE REGULAR · DON'T SERVE", hint_fridge: "NOT AFTER 03:40!", hint_disguise: "No shadow...",
    daily: n => `DAILY SHIFT #${n} ▶`, dailyDone: "Today's shift is done. Come back tomorrow!", dailyRow: n => `Daily #${n}`,
    dailyIntro: ["Tonight everyone works the same store.", "One try. You know the rules."], cause_daily: "Survived the night", over_daily: "DAILY CLEARED",
    dailyShare: (n, ok, pay, cause) => `ONE MORE SHIFT · Daily #${n}\n${ok ? "🟩 Clocked out" : "🟥 " + cause}  ${pay}`,
    cont_btn: "CONTINUE", cont_cost: c => `Continue costs ${c}`, x3: "x3",
    hint: "Move: arrows/tap  Work: Space/tap  Look: ↑ or tap door",
    quotaLine: q => `Quota ${q}`, lookHint: "▲ LOOK AT IT!",
    serve: "RING UP", restock: "RESTOCK", pickup: "PICK UP",
    strike: "Complaint!", clockout: "CLOCKED OUT", bonus: "Shift bonus",
    cause_door: "Looked away", cause_quota: "Missed the quota", cause_clock: "Moved at 03:33", cause_regular: "Served the Regular", cause_fridge: "Opened the fridge", cause_knock: "The door opened", cause_lamp: "Looked at the lamp",
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
