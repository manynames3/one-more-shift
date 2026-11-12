// Run state, settings and translations.
const store = {
  get(k, d) { try { const v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); } catch { return d; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* private mode */ } },
};

// Pay matches the show: each gig pays a multiple of the 2026 minimum wage (₩10,320 an hour), taken
// from the show's gig in the same slot: store 50x (episode 1, ₩4M a night), event 75x (episode 2's
// ₩6M a day, scaled by the same rate), delivery 200x (episode 3's milk run), cinema 100x (no figure in
// the show; 100x is what the agency offers after the first job), construction 500x (set by design).
// A shift is one in-game hour, so a cleared shift pays one hour at that rate.
export const MIN_WAGE = 10320;
export const MULT = { 1: 50, 2: 75, 3: 200, 4: 100, 5: 150, 6: 500 };
export const hourly = act => MIN_WAGE * (MULT[act] || 50);
export const START_DEBT = 40000000;

export const S = {
  lang: store.get("oms.lang", (navigator.language || "en").toLowerCase().startsWith("ko") ? "ko" : "en"),
  muted: store.get("oms.muted", false),
  best: store.get("oms.best", 0),
  runs: store.get("oms.runs", 0),
  seen: store.get("oms.seen", {}),     // rules whose first-time hint the player has survived
  acts: store.get("oms.acts", {}),
  notes: store.get("oms.notes", {}),     // the Regular's notes found, by act
  endings: store.get("oms.endings", {}), // endings seen     // story acts cleared, e.g. { 1: true } once the Rat King is beaten
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
  { n: 4, key: "cinema", built: true },
  { n: 5, key: "trial", built: true },
  { n: 6, key: "site", built: true },
  { n: 7, key: "park", built: true },
];
export function saveNote(act) { S.notes[act] = true; store.set("oms.notes", S.notes); }
export const notesFound = () => [1, 2, 3, 4, 5, 6].filter(n => S.notes[n]).length;
export function saveEnding(k) { S.endings[k] = true; store.set("oms.endings", S.endings); }

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
// Act 4, the cinema: the screen (1), the audience count (2), the film that isn't on the schedule (3).
export const CRULES = ["screen", "count", "unscheduled"];
export const crulesFor = shift => CRULES.slice(0, Math.min(shift, CRULES.length));
// Act 5, the trial: blue pills only (1), stay in bed after lights-out (2), no name tag, no arm (3).
export const WRULES = ["pill", "bed", "nurse"];
export const wrulesFor = shift => WRULES.slice(0, Math.min(shift, WRULES.length));
// Act 6, the site: the occupied hoist (1), the pour (2), roll call (3).
export const SRULES = ["hoist", "pit", "rollcall"];
export const srulesFor = shift => SRULES.slice(0, Math.min(shift, SRULES.length));

/** Per-act setup: which scene runs the shift, the place on the job card, the manager's lines. */
export const GIG = {
  1: { scene: "Shift", place: "place", intro: "intro", briefs: { 2: "brief2", 3: "brief3", 4: "brief4", 5: "brief5", 6: "brief6", 7: "brief7" } },
  2: { scene: "Event", place: "place2", intro: "e_intro", briefs: { 2: "e_brief2", 3: "e_brief3" }, rules: ERULES },
  3: { scene: "Delivery", place: "place3", intro: "d_intro", briefs: { 2: "d_brief2", 3: "d_brief3" }, rules: DRULES },
  5: { scene: "Ward", place: "place5", intro: "w_intro", briefs: { 2: "w_brief2", 3: "w_brief3" }, rules: WRULES },
  6: { scene: "Site", place: "place6", intro: "s_intro", briefs: { 2: "s_brief2", 3: "s_brief3" }, rules: SRULES },
  7: { scene: "Park", place: "place7", intro: "k_intro", briefs: {}, rules: ["all"] },
  4: { scene: "Cinema", place: "place4", intro: "c_intro", briefs: { 2: "c_brief2", 3: "c_brief3" }, rules: CRULES },
};

export function won(n) { return "₩" + Math.max(0, Math.round(n)).toLocaleString("en-US"); }

const STR = {
  ko: {
    board: "새벽인력 · 일자리 게시판", act: n => `${n}막`, st_clear: "완료", st_open: "모집 중", st_soon: "준비 중", st_locked: "잠김",
    job_store: "편의점", job_event: "행사", job_delivery: "배달", job_cinema: "극장", job_trial: "임상시험", job_site: "공사장", job_park: "놀이공원",
    jd_store: "사흘 밤을 버티고 쥐왕을 쓰러뜨려라", jd_soon: "다음 업데이트에서 문을 엽니다", jd_locked: "앞의 일을 먼저 끝내세요",
    jd_keep: "계속 근무: 편의점 다음 교대", board_clear: "곽 실장: 준호? 모르는 이름인데. 다음 일이나 보자.", act_clear: n => `${n}막 완료`, board_clear2: "곽 실장: 수고했어. 다음 일 줄게.",
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
    rule_boss2: "빈 탈에 풍선 다섯 개를 묶으시오", cause_suit: "빈 탈에게 붙잡혔다", suitTurn: "...머리가 없어도 공연은 계속된다.",
    suitTies: (n, m) => `풍선 ${n}/${m}`, hint_tie: "풍선을 들고, 비틀거릴 때 묶어! (Space)", hint_tieNow: "지금! 묶어!",
    clue_suit: "무대 위 탈 머리 안쪽 세탁표: '담당 준호'",
    rule_boss3: "깜빡이지 않는 계단으로 오르시오", cause_resident: "주민에게 붙잡혔다", chaseStart: "위층에서 누가 내려온다. 옥상으로!",
    hint_flight: "깜빡이는 쪽은 안 돼! ← →", hint_phone: "Space: 휴대폰 줍기", roofF: "옥상",
    clue_phone: "낡은 폴더폰. 주문 47건, 전부 발신자 '준호'.",
    place4: "별빛극장 야간", jd_cinema: "사흘 밤 극장 지키기 · 안내원을 조심",
    rule_screen: "화면을 3초 이상 보지 마시오", rule_count: "더 많이 나오면 3관을 잠그시오", rule_unscheduled: "상영표에 없는 영화엔 영사실 금지",
    rule_boss4: "불을 끄고 어둠 속에서 치시오",
    cause_screen: "화면을 너무 오래 봤다", cause_count: "3관을 잠그지 않았다", cause_booth: "영사실에 올라갔다", cause_usher: "안내원에게 붙잡혔다",
    c_intro: ["별빛극장 야간이야. 표 팔고,", "상영 끝나면 3관 청소.", "필름 끝나면 영사실 가서 갈아 끼우고.", "아, 영화는 보지 마. 3초 이상은."],
    c_brief2: ["3관에 들어간 손님 수를 세.", "나온 사람이 더 많으면... 문 잠가."],
    c_brief3: ["상영표에 없는 영화가 걸리면,", "영사실엔 올라가지 마. 절대로."],
    hint_look: "화면 보지 마! →", hint_lock: "더 나왔다! 3관 잠가 (Space)", hint_cctv: "상영표에 없는 영화... 영사실 금지",
    hallIn: n => `3관 입장 ${n}명`, nowShowing: "상영 중", intermission: "휴식", filmBroke: "필름 끊김!",
    usherStart: "영사기가 저절로 켜졌다. 빛 속에서 누가 걸어 나온다.", usherHp: n => `안내원 ${n}`, hint_lamp: "Space: 영사기 끄기", hint_hit: "지금! 어둠 속에서 쳐!",
    clue_cctv: "화면 속 CCTV, 계산대 뒤에 선 남자. 명찰: 준호.",
    place5: "해맑음병원 임상시험", place6: "새벽 공사장",
    jd_trial: "사흘 밤 임상시험 · 3번 침대를 조심", jd_site: "사흘 밤 공사장 · 감독관을 조심",
    rule_pill: "파란 약만 드시오", rule_bed: "소등 후엔 침대에 있으시오", rule_nurse: "이름표 없는 간호사는 피하시오",
    rule_boss5: "등을 돌렸을 때만 움직여 문으로", cause_pill: "빨간 약을 먹었다", cause_bed: "소등 중에 침대를 나왔다", cause_nurse: "이름표 없는 간호사", cause_subject: "3번 피험자에게 붙잡혔다",
    w_intro: ["이번엔 임상시험이야.", "누워만 있으면 돼.", "주는 약 먹고, 일지 쓰고, 피 뽑고.", "파란 약만 먹어. 빨간 건 돌려보내."],
    w_brief2: ["불 꺼지면 침대에서 나오지 마.", "화장실? 참아."],
    w_brief3: ["이름표 없는 간호사가 오면...", "팔 내밀지 마. 그런 간호사는 없어."],
    hint_pill: "Space: 약 먹기", hint_red: "빨간 약! 먹지 말고 기다려", hint_bed: "소등! 침대로, 가만히!", hint_arm: "침대에서 Space: 채혈", hint_notag: "이름표가 없다... 팔 내밀지 마",
    missedDose: "투약 누락!", subjectNo: "피험자 9번",
    subjectStart: "3번 침대가 일어났다. 문 앞에 서 있다.", hint_sneak: "돌아보면 멈춰! 문에서 Space",
    clue_trial: "문 옆 피험자 명단: 7번 준호 · 상태 '진행 중'.",
    rule_hoist: "누가 탄 호이스트엔 싣지 마시오", rule_pit: "타설 중엔 구덩이를 건너지 마시오", rule_rollcall: "점호가 많으면 판을 뒤집으시오",
    rule_boss6: "갈고리 아래로 유인하시오", cause_hoist: "누가 탄 호이스트에 실었다", cause_pit: "타설 중 구덩이 위에 섰다", cause_rollcall: "점호판을 안 뒤집었다", cause_foreman: "감독관에게 맞았다",
    s_intro: ["공사장이야. 벽돌 날라서 호이스트에.", "시급이 제일 세. 그만큼 위험하고.", "호이스트에 누가 타고 내려오면...", "싣지 마."],
    s_brief2: ["타설할 땐 구덩이 건너지 마.", "콘크리트가 뭘 덮는지는 묻지 말고."],
    s_brief3: ["점호판 숫자가 명단보다 하나 많으면,", "판을 뒤집어. 그 하나는 세지 마."],
    hint_pile: "Space: 벽돌 들기", hint_hoistGo: "→ 호이스트에 싣기", hint_rider: "안에 누가 있다! 싣지 마", hint_pour: "타설! 구덩이에서 떨어져", hint_roll: "하나 많다! 판 뒤집기 (Space)",
    rollBoard: (n, m) => `점호 ${n}\n명단 ${m}`, holdBrick: "벽돌", foremanStart: "감독관이 망치를 들었다.", foremanHp: n => `감독관 ${n}`, hint_crane: "갈고리 밑으로 유인, Space: 낙하",
    clue_site: "감독관의 사원증. 사진 속 얼굴: 준호.",
    place7: "달빛랜드 퍼레이드", jd_park: "마지막 일 · 한 번만 더", wageAll: "남은 빚 전액", rule_all: "지금까지 배운 규칙을 모두 지키시오",
    k_intro: ["마지막 일이야.", "달빛랜드 야간 퍼레이드.", "남은 빚은 내가 전부 갚아 줄게.", "한 번만 더."],
    rule_float: "빨간 불 켠 수레는 보지 마시오", rule_still: "불이 꺼지면 움직이지 마시오", rule_boss7: "05:00까지 살아남으시오",
    cause_float: "빨간 수레를 봤다", cause_still: "어둠 속에서 움직였다", cause_kwak: "곽 실장에게 붙잡혔다",
    hint_float: "빨간 수레! 그쪽 보지 마", hint_still: "불이 꺼진다! 멈춰", hint_junho: "Space: 준호?", hint_survive: "피해! 05:00까지",
    parkStart: "폐장한 놀이공원. 퍼레이드는 아직 돌고 있다.", junhoSeen: "회전목마 옆에 누가 앉아 있다.",
    junhoLine: "준호: 소라야... 왔구나. 아무것도 서명하지 마. 아무것도.",
    offer: ["곽 실장: 수고했어, 소라 씨. 진짜로.", "곽 실장: 약속대로 빚은 전부 없애 줄게.", "곽 실장: 대신 한 번만 더. 내일부터 프런트 데스크야.", "곽 실장: 새로 오는 사람들한테 규칙만 나눠 주면 돼."],
    choiceSign: "서명한다", choiceRefuse: "거절한다", choiceNote: "쪽지를 건넨다",
    kwakTurn: "곽 실장: ...그래? 그럼 퇴근은 못 시켜 주지.", notesSlip: n => `단골의 쪽지 ${n}/6`,
    note1: "단골의 쪽지: '규칙은 너를 지키려고 있는 게 아니야.'", note2: "단골의 쪽지: '탈 속엔 처음부터 아무도 없었어.'", note3: "단골의 쪽지: '4층엔 내가 살았었지.'",
    note4: "단골의 쪽지: '그 CCTV, 나도 찍혀 있어.'", note5: "단골의 쪽지: '난 7번 다음, 8번이었어.'", note6: "단골의 쪽지: '곽 실장 자리는 원래 내 자리였어.'",
    end_sign: "엔딩 · 프런트 데스크", end_walk: "엔딩 · 퇴근", end_note: "숨겨진 엔딩 · 단골의 쪽지",
    endLines_sign: ["빚은 0원이 됐다.", "다음 날 밤, 소라는 새 사람에게 규칙이 적힌 종이를 건넸다.", "\"일은 간단해요. 규칙만 지키면.\"", "출근 기록은 있었다. 퇴근 기록은 없었다."],
    endLines_walk: ["05:00. 곽 실장은 종이 더미가 되어 흩어졌다.", "소라와 준호는 새벽 거리로 걸어 나왔다.", "빚은 그대로다. 그래도 둘 다 퇴근했다.", "등 뒤에서 새벽인력 간판이 꺼졌다."],
    endLines_note: ["소라는 단골의 쪽지 여섯 장을 내밀었다.", "단골이 웃었다. \"내 자리야. 내가 앉을게.\"", "단골은 새벽인력이 처음 데려간 알바생이었다.", "그날 이후 새벽인력은 아무도 부르지 않았다."],
    credits: ["한 번만 더", "비영리 팬 게임", "넷플릭스 「꿀알바」에서 영감을 받았습니다", "캐릭터·규칙·괴물은 이 게임의 창작입니다", "", "기획·개발 · Ai", "아트 · 픽셀 도트 작업", "음악·효과음 · 직접 합성", "", "끝까지 일해 줘서 고마워요"],
    m_pump: "헬륨 충전 · 꾹 눌렀다 떼기", m_reel: "필름 걸기 · 초록에 3번", m_still: "가만히... 꾹 누르고 있기", m_stack: "초록에 맞춰 내려놓기", popped: "펑!", again: "다시!", bricksFell: "와르르!", hint_pump: "꾹 눌러 채우고, 초록에서 떼!",
    spilled: "쏟았다!", hint_hop: "Space·터치: 라바콘 점프!",
    suitPhase2: "탈이 더 빨라졌다. 두 번 덮친다!", resPhase2: "반대쪽에도 눈이... 깜빡이는 전구만 믿어.", usherPhase2: "안내원이 빨라졌다. 어둠이 짧다!", subjectPhase2: "문이 가까워질수록, 그것은 자주 돌아본다.", foremanPhase2: "감독관이 미쳐 날뛴다. 두 번 내려친다!", kwakPhase2: "곽 실장의 계약서에 불이 붙었다!",
    who_sora: "소라", who_kwak: "곽 실장", who_junho: "준호", who_regular: "단골",
    talk_suit: [["sora", "scared", "...떨어진 탈 머리 안쪽에 뭐가 붙어 있다."], ["sora", "neutral", "세탁표. '담당 준호'. ...오빠 이름이다."]],
    talk_phone: [["sora", "scared", "오빠 폴더폰이다. 2년 전에 잃어버렸다던."], ["sora", "tired", "주문 47건... 전부 이 폰에서 들어왔어."], ["junho", "sad", "(음성 메시지) 소라야. 이 번호로 오는 일은 받지 마."]],
    talk_cctv: [["sora", "scared", "영화가 아니라 CCTV였어. 편의점 계산대..."], ["sora", "determined", "계산대 뒤의 저 사람. 오빠야. 오빠도 거기서 일했어."]],
    talk_trial: [["sora", "tired", "문 옆 피험자 명단. 7번, 준호. 상태: 진행 중."], ["regular", "smile", "(복도 끝에서) 8번은 나였어."]],
    talk_site: [["sora", "scared", "감독관 목에 걸린 사원증... 사진 속 얼굴이 오빠야."], ["kwak", "sly", "(전화) 소라 씨, 수고했어. 마지막 일이 하나 남았어."]],
    talk_junho: [["junho", "sad", "소라야... 왔구나."], ["sora", "relieved", "오빠! 2년 동안 어디 있었어!"], ["junho", "tired", "퇴근을 못 했어. 빚 갚아 준다는 말에 서명했거든."], ["junho", "neutral", "아무것도 서명하지 마. 아무것도."]],
    talk_offer: [["kwak", "smile", "수고했어, 소라 씨. 진짜로."], ["kwak", "smile", "약속대로 빚은 전부 없애 줄게."], ["kwak", "sly", "대신 한 번만 더. 내일부터 프런트 데스크야."], ["kwak", "sly", "새로 오는 사람들한테 규칙만 나눠 주면 돼."]],
    place2: "그랜드 오픈 행사", banner: "만두군 쇼",
    rule_balloon: "풍선은 아이에게만 주시오", rule_head: "탈이 벗겨지면 무대를 보지 마시오", rule_answer: "탈이 부르면 대답하지 마시오",
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
    jd_keep: "Keep working: next shift at the store", board_clear: "Kwak: Junho? Never heard of him. Let's find your next job.", act_clear: n => `ACT ${n} CLEAR`, board_clear2: "Kwak: Good work. Here's the next one.",
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
    rule_boss2: "Tie five balloons to the empty suit", cause_suit: "Caught by the empty suit", suitTurn: "...The show goes on without a head.",
    suitTies: (n, m) => `BALLOONS ${n}/${m}`, hint_tie: "Hold a balloon, tie it on when it reels (Space)", hint_tieNow: "NOW! TIE IT!",
    clue_suit: "Laundry tag inside the head on the stage: 'handled by JUNHO'",
    rule_boss3: "Climb the flight that ISN'T flickering", cause_resident: "Caught by the Resident", chaseStart: "Something's coming down. Get to the roof!",
    hint_flight: "Not the flickering side! ← →", hint_phone: "Space: pick up the phone", roofF: "ROOF",
    clue_phone: "An old flip phone. 47 orders, every one placed by 'JUNHO'.",
    place4: "Starlight Cinema", jd_cinema: "Three nights at the cinema · mind the Usher",
    rule_screen: "Don't stare at the screen (3s)", rule_count: "More out than in? Lock Hall 3", rule_unscheduled: "Unlisted film? Avoid the booth",
    rule_boss4: "Cut the lamp, hit it in the dark",
    cause_screen: "Watched the screen", cause_count: "Didn't lock Hall 3", cause_booth: "Went up to the booth", cause_usher: "Caught by the Usher",
    c_intro: ["Starlight Cinema. Sell tickets,", "clean Hall 3 after each film,", "change the reel up in the booth.", "And don't watch. Not over 3 seconds."],
    c_brief2: ["Count who goes into Hall 3.", "If more come out... lock the door."],
    c_brief3: ["If a film not on the schedule runs,", "don't go up to the booth. Ever."],
    hint_look: "Don't watch! →", hint_lock: "One too many! Lock Hall 3 (Space)", hint_cctv: "Not on the schedule... stay out of the booth",
    hallIn: n => `HALL 3 IN: ${n}`, nowShowing: "SHOWING", intermission: "BREAK", filmBroke: "Film broke!",
    usherStart: "The projector came on by itself. Someone walks out of the light.", usherHp: n => `USHER ${n}`, hint_lamp: "Space: cut the lamp", hint_hit: "NOW! Hit it in the dark!",
    clue_cctv: "On the CCTV film, a man behind a counter. Name tag: JUNHO.",
    place5: "Haemalgeum Trial", place6: "Dawn Site",
    jd_trial: "Three nights in a drug trial · watch bed 3", jd_site: "Three nights on site · watch the Foreman",
    rule_pill: "Blue pills only", rule_bed: "After lights-out, stay in bed", rule_nurse: "No name tag? Don't give your arm",
    rule_boss5: "Move only while its back is turned", cause_pill: "Took the red pill", cause_bed: "Left bed after lights-out", cause_nurse: "The nurse with no tag", cause_subject: "Caught by subject 3",
    w_intro: ["A drug trial. Just lie there.", "Pills, the diary, a blood draw.", "Blue pills only.", "Send the red ones back."],
    w_brief2: ["When the lights go out, stay in bed.", "Bathroom? Hold it."],
    w_brief3: ["If a nurse with no name tag comes,", "keep your arm. No such nurse."],
    hint_pill: "Space: take the pill", hint_red: "Red pill! Don't take it, wait", hint_bed: "Lights out! To bed, stay still!", hint_arm: "Space at your bed: blood draw", hint_notag: "No name tag... keep your arm",
    missedDose: "Missed dose!", subjectNo: "SUBJECT 9",
    subjectStart: "Bed 3 got up. It's standing at the door.", hint_sneak: "Freeze when it turns! Space at the door",
    clue_trial: "Subject list by the door: No. 7 JUNHO · status 'ongoing'.",
    rule_hoist: "Never load a hoist with a rider", rule_pit: "During a pour, stay off the pit", rule_rollcall: "One too many at roll call? Flip it",
    rule_boss6: "Lure it under the hook, signal", cause_hoist: "Loaded the occupied hoist", cause_pit: "On the pit during a pour", cause_rollcall: "Didn't flip the board", cause_foreman: "Hit by the Foreman",
    s_intro: ["Building site. Bricks to the hoist.", "Best pay you'll see. Worst risk too.", "If the hoist comes down with someone", "in it... don't load it."],
    s_brief2: ["During a pour, don't cross the pit.", "Don't ask what the concrete covers."],
    s_brief3: ["Roll call one more than the list?", "Flip the board. Don't count it."],
    hint_pile: "Space: pick up bricks", hint_hoistGo: "→ Load the hoist", hint_rider: "Someone's inside! Don't load", hint_pour: "Pour! Off the pit", hint_roll: "One too many! Flip it (Space)",
    rollBoard: (n, m) => `ROLL ${n}\nLIST ${m}`, holdBrick: "BRICKS", foremanStart: "The Foreman picks up his hammer.", foremanHp: n => `FOREMAN ${n}`, hint_crane: "Lure under the hook, Space: drop",
    clue_site: "The Foreman's staff ID. The photo is JUNHO.",
    place7: "Moonlight Land", jd_park: "The last job · one more shift", wageAll: "All your debt", rule_all: "Keep every rule you've learned",
    k_intro: ["Last job. The night parade", "at Moonlight Land.", "Do it and I'll clear what you owe.", "All of it. One more shift."],
    rule_float: "Don't look at the red-lit float", rule_still: "When the lights go out, don't move", rule_boss7: "Survive until 05:00",
    cause_float: "Looked at the red float", cause_still: "Moved in the dark", cause_kwak: "Caught by Kwak",
    hint_float: "Red float! Face away", hint_still: "Lights going out! Freeze", hint_junho: "Space: Junho?", hint_survive: "Dodge! Until 05:00",
    parkStart: "A park that closed years ago. The parade still runs.", junhoSeen: "Someone is sitting by the carousel.",
    junhoLine: "Junho: Sora... you came. Don't sign anything. Anything.",
    offer: ["Kwak: Good work, Sora. Really.", "Kwak: As promised, I'll wipe out your debt.", "Kwak: Just one more shift. The front desk, from tomorrow.", "Kwak: All you do is hand new people the rules."],
    choiceSign: "SIGN", choiceRefuse: "REFUSE", choiceNote: "GIVE NOTES",
    kwakTurn: "Kwak: ...Is that so? Then you don't get to clock out.", notesSlip: n => `NOTES ${n}/6`,
    note1: "The Regular's note: 'The rules aren't there to protect you.'", note2: "The Regular's note: 'Nobody was ever inside the suit.'", note3: "The Regular's note: 'I used to live on the 4th floor.'",
    note4: "The Regular's note: 'I'm on that CCTV too.'", note5: "The Regular's note: 'I was subject 8, after him.'", note6: "The Regular's note: 'Kwak's desk used to be mine.'",
    end_sign: "ENDING · FRONT DESK", end_walk: "ENDING · CLOCKED OUT", end_note: "SECRET ENDING · THE REGULAR'S NOTE",
    endLines_sign: ["The debt hit zero.", "The next night, Sora handed a new hire a sheet of rules.", "\"The job is simple. Just keep the rules.\"", "There was a clock-in record. There was no clock-out."],
    endLines_walk: ["05:00. Kwak came apart into a pile of contracts.", "Sora and Junho walked out into the dawn.", "The debt is still there. But they both clocked out.", "Behind them, the agency sign went dark."],
    endLines_note: ["Sora held out the Regular's six notes.", "The Regular smiled. \"It's my seat. I'll take it.\"", "The Regular was the first worker the agency ever took.", "After that night, the agency never called anyone again."],
    credits: ["ONE MORE SHIFT", "A non-commercial fan game", "Inspired by Netflix's Dead-End Job (꿀알바)", "Characters, rules and monsters are this game's own", "", "Design & code · Ai", "Pixel art", "Music & sound · synthesized", "", "Thanks for working every shift"],
    m_pump: "HELIUM · hold, let go", m_reel: "THREAD · 3 in the green", m_still: "HOLD STILL · keep holding", m_stack: "DROP IN THE GREEN", popped: "POP!", again: "Again!", bricksFell: "CRASH!", hint_pump: "Hold to fill, let go in the green!",
    spilled: "Spilled!", hint_hop: "Space/tap: hop the cones!",
    suitPhase2: "It's faster now. It lunges twice!", resPhase2: "An eye on both sides... trust only the flickering bulb.", usherPhase2: "The Usher speeds up. The dark is shorter!", subjectPhase2: "The closer the door, the more it looks back.", foremanPhase2: "The Foreman goes wild. Two swings!", kwakPhase2: "Kwak's contracts catch fire!",
    who_sora: "SORA", who_kwak: "KWAK", who_junho: "JUNHO", who_regular: "THE REGULAR",
    talk_suit: [["sora", "scared", "...Something's stuck inside the fallen head."], ["sora", "neutral", "A laundry tag. 'Handled by JUNHO.' ...My brother's name."]],
    talk_phone: [["sora", "scared", "Junho's flip phone. The one he 'lost' two years ago."], ["sora", "tired", "Forty-seven orders... all from this phone."], ["junho", "sad", "(voicemail) Sora. If a job comes from this number, don't take it."]],
    talk_cctv: [["sora", "scared", "It wasn't a film. It was CCTV. A store counter..."], ["sora", "determined", "The man behind it is Junho. He worked there too."]],
    talk_trial: [["sora", "tired", "The subject list by the door. No. 7, Junho. Status: ongoing."], ["regular", "smile", "(from the end of the hall) I was No. 8."]],
    talk_site: [["sora", "scared", "The Foreman's staff ID... the photo is Junho."], ["kwak", "sly", "(phone) Good work, Sora. One last job left."]],
    talk_junho: [["junho", "sad", "Sora... you came."], ["sora", "relieved", "Junho! Where have you been for two years?"], ["junho", "tired", "I never clocked out. I signed, to clear my debt."], ["junho", "neutral", "Don't sign anything. Anything."]],
    talk_offer: [["kwak", "smile", "Good work, Sora. Really."], ["kwak", "smile", "As promised, I'll wipe out your debt."], ["kwak", "sly", "Just one more shift. The front desk, from tomorrow."], ["kwak", "sly", "All you do is hand new people the rules."]],
    place2: "Grand Opening", banner: "MANDU SHOW",
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
