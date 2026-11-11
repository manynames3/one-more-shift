// 덕구 (Deokgu), the coworker who works shifts 1-3 with you, and what he really is.
//
// Shift 1-2: he stands by the shelves and gives advice.
// Shift 3:   he gets hungry. No shadow. At 03:45 the customers run and he turns into the Rat King.
// The fight: it spawns rats, rears up (telegraph), and lunges along a red line. After a lunge it's
// dazed; that's the only time the mop hurts it. Three hits on you and you're done. Six on it and you live.
import Phaser from "phaser";
import { W, H, BAR, C, txt, rand } from "../ui.js";
import { S, t } from "../state.js";
import * as snd from "../audio.js";

export const BOSS_SHIFT = 3, BOSS_MIN = 45;
const SPOT = { x: 56, y: 151 };           // where Deokgu stands
const ARENA = { top: 122, bot: 154, xl: y => 100 - (y - 118) * 1.45 + 6, xr: y => Math.min(236, 213 + (y - 118) * 1.3) - 4 };
const PLAYER_HP = 3, BOSS_HP = 6;

export const BossMixin = {
  initBoss() {
    this.boss = null;
    this.deokgu = null;
    if (this.run.daily || this.run.shift > BOSS_SHIFT) return;
    const dg = this.makeChar("deokgu", SPOT.x, SPOT.y);
    dg.setFrame("right_walk_0");
    this.deokgu = dg;
    this.dgLines = t("dg" + this.run.shift);
    this.dgIdx = 0; this.dgT = 4;
    this.dgBubble = txt(this, 0, 0, "", { ox: 0.5, size: 9, color: C.white, depth: 630 }).setVisible(false);
    this.dgBubble.setBackgroundColor("#14101a").setPadding(3, 1, 3, 1);
    if (this.run.shift === BOSS_SHIFT) { dg.sh.setVisible(false); this.dgGlitch = 2; }
  },

  bossActive() { return this.boss && this.boss.phase !== "done"; },

  tickDeokgu(dt) {
    const dg = this.deokgu;
    if (!dg || this.bossActive()) return;
    this.syncChar(dg);
    if (this.run.shift === BOSS_SHIFT) {            // something is wrong with him tonight
      this.dgGlitch -= dt;
      if (this.dgGlitch <= 0) {
        this.dgGlitch = rand(1.2, 2.8);
        dg.setTintFill(0x3b2418);
        this.time.delayedCall(90, () => dg.active && dg.clearTint());
      }
    }
    this.dgT -= dt;
    if (this.dgT <= 0 && this.dgIdx < this.dgLines.length) {
      this.say(this.dgLines[this.dgIdx++], 3.2);
      this.dgT = rand(9, 13);
    }
    if (this.dgBubble.visible) {
      const half = this.dgBubble.width / 2 + 2;
      this.dgBubble.setPosition(Phaser.Math.Clamp(Math.round(dg.x), half, W - half), Math.round(dg.y) - 60);
    }
  },

  say(line, secs) {
    this.dgBubble.setText(line).setVisible(true);
    snd.sfx("type");
    this.time.delayedCall(secs * 1000, () => this.dgBubble.active && this.dgBubble.setVisible(false));
  },

  // ---------------------------------------------------------------- start
  startBoss() {
    const dg = this.deokgu;
    this.boss = { phase: "intro", t: 2.6, hp: BOSS_HP, state: "idle", st: 1.2, ratT: 0.6, line: null, vx: 0, vy: 0 };
    this.php = PLAYER_HP; this.inv = 0; this.swingCd = 0; this.rats = [];
    // stop everything else: the customers run, the jobs can wait
    this.cancelWork(); this.intent = null; this.target = null;
    if (this.room !== "floor") this.enterRoom("floor", { x: 214, y: 146 }, { face: "left" });
    this.behind = false;
    this.tweens.add({ targets: this.p, x: 214, y: 146, duration: 600, onUpdate: () => this.syncChar(this.p) });
    this.face = "left";
    this.watch.state = "idle"; this.watch.t = 999; this.ent.setVisible(false); this.eyes.setVisible(false);
    this.vigDark.setVisible(false); this.flick.setAlpha(0);
    for (const c of this.customers) { if (!c.out) { c.out = true; c.bar.clear(); } }
    this.queue.length = 0;
    Object.values(this.tasks).forEach(k => { k.active = false; k.mark.setVisible(false); });
    snd.music("off"); snd.ambience(false); snd.sfx("warn");
    this.say(t("dgTurn"), 2.2);
    this.tweens.add({ targets: dg, x: 110, y: 138, duration: 1300, onUpdate: () => this.syncChar(dg) });
    this.cameras.main.shake(2400, 0.003);

    // HUD for the fight
    this.fightPlate = this.add.rectangle(0, BAR, W, 15, 0x14101a, 0.88).setOrigin(0).setDepth(893);
    this.hearts = [0, 1, 2].map(i => this.add.image(10 + i * 13, BAR + 7, "props_icons", "heart").setDepth(895));
    this.bossName = txt(this, W - 128, BAR + 2, t("ratking"), { ox: 1, size: 9, color: C.red, depth: 895 });
    this.bossBarBg = this.add.rectangle(W - 70, BAR + 7, 112, 7, 0x14101a).setStrokeStyle(1, 0xf6f1e7).setDepth(894);
    this.bossBar = this.add.rectangle(W - 124, BAR + 7, 108, 3, 0xef3b4a).setOrigin(0, 0.5).setDepth(895);
    [this.fightPlate, this.hearts, this.bossBarBg, this.bossBar, this.bossName].flat().forEach(o => o.setAlpha(0));
    this.lineG = this.add.graphics().setDepth(4);
    this.swingFx = this.add.sprite(0, 0, "boss_fx", "swing_0").setDepth(627).setVisible(false);
    this.mop = this.add.image(0, 0, "boss_mop").setOrigin(0.5, 1).setDepth(628).setVisible(false);
  },

  transform() {
    const dg = this.deokgu, b = this.boss;
    this.cameras.main.flash(300, 255, 255, 255);
    snd.sfx("roar"); snd.music("boss");
    this.dgBubble.setVisible(false);
    b.spr = this.add.sprite(dg.x, dg.y + 4, "boss_ratking", "idle_0").setOrigin(0.5, 0.92);
    b.spr.sh = this.add.image(dg.x, dg.y + 2, "props_shadow_blob").setScale(2.6, 1.6).setAlpha(0.7);
    dg.sh.destroy(); dg.destroy(); this.deokgu = null;
    for (let i = 0; i < 4; i++) this.spawnRat(b.spr.x + rand(-20, 20), b.spr.y);
    [this.fightPlate, this.hearts, this.bossBarBg, this.bossBar, this.bossName].flat().forEach(o => o.setAlpha(1));
    this.hint("fight", W / 2, 132);
    b.phase = "fight"; b.state = "idle"; b.st = 1.0;
  },

  // ---------------------------------------------------------------- tick
  tickBoss(dt) {
    const b = this.boss;
    if (b.phase === "intro") {
      b.t -= dt;
      if (this.deokgu) this.syncChar(this.deokgu);
      if (b.t <= 0) this.transform();
      return;
    }
    if (b.phase !== "fight") return;
    const spr = b.spr, p = this.p, angry = b.hp <= BOSS_HP / 2;
    this.inv = Math.max(0, this.inv - dt);
    this.swingCd = Math.max(0, this.swingCd - dt);
    p.setAlpha(this.inv > 0 && Math.floor(this.inv * 12) % 2 ? 0.4 : 1);

    b.st -= dt;
    switch (b.state) {
      case "idle":
        spr.play("boss_ratking_idle", true);
        b.ratT -= dt;
        if (b.ratT <= 0 && this.rats.length < (angry ? 7 : 4)) { this.spawnRat(spr.x + rand(-18, 18), spr.y - 2); b.ratT = angry ? 0.55 : 0.9; snd.sfx("squeak"); }
        if (b.st <= 0) {
          b.state = "tell"; b.st = angry ? 0.6 : 0.85;
          b.line = { x: p.x, y: Phaser.Math.Clamp(p.y, ARENA.top, ARENA.bot) };
          spr.anims.stop(); spr.setFrame("tell"); snd.sfx("roar");
        }
        break;
      case "tell": {
        // a red line shows exactly where it will go
        this.lineG.clear().lineStyle(3, 0xef3b4a, Math.floor(b.st * 10) % 2 ? 0.9 : 0.4)
          .lineBetween(spr.x, spr.y - 6, b.line.x, b.line.y - 6);
        if (b.st <= 0) {
          const dx = b.line.x - spr.x, dy = b.line.y - spr.y, d = Math.hypot(dx, dy) || 1;
          const speed = angry ? 290 : 235;
          b.vx = dx / d * speed; b.vy = dy / d * speed; b.left = d + 30;
          b.state = "dash"; spr.setFrame("dash"); this.lineG.clear(); snd.sfx("dash");
        }
        break;
      }
      case "dash": {
        const step = Math.min(b.left, Math.hypot(b.vx, b.vy) * dt);
        const k = step / Math.hypot(b.vx, b.vy);
        let nx = spr.x + b.vx * k, ny = Phaser.Math.Clamp(spr.y + b.vy * k, ARENA.top, ARENA.bot);
        nx = Phaser.Math.Clamp(nx, ARENA.xl(ny), ARENA.xr(ny));
        const blocked = Math.abs(nx - (spr.x + b.vx * k)) > 0.5 || Math.abs(ny - (spr.y + b.vy * k)) > 0.5;
        spr.setPosition(nx, ny); b.left -= step;
        if (Math.abs(spr.x - p.x) < 15 && Math.abs(spr.y - p.y) < 9) this.hurtPlayer();
        if (b.left <= 0 || blocked) {
          b.state = "stun"; b.st = angry ? 1.3 : 1.7;
          spr.play("boss_ratking_stun", true); this.cameras.main.shake(160, 0.006); snd.sfx("stamp");
          this.stars = this.stars || this.add.sprite(0, 0, "boss_fx", "star_0").setDepth(629);
          this.stars.setVisible(true).play("boss_fx_star", true);
        }
        break;
      }
      case "stun":
        if (this.stars) this.stars.setPosition(spr.x, spr.y - 60);
        if (b.st <= 0) { b.state = "idle"; b.st = angry ? 0.8 : 1.3; if (this.stars) this.stars.setVisible(false); }
        break;
      case "hurt":
        if (b.st <= 0) { b.state = "stun"; b.st = 0.5; spr.play("boss_ratking_stun", true); }
        break;
    }
    spr.setDepth(spr.y); spr.sh.setPosition(spr.x, spr.y + 2).setDepth(spr.y - 0.5);
    if (b.state === "idle" || b.state === "stun") {
      // keep it lurching towards you between lunges
      const dx = p.x - spr.x, dy = p.y - spr.y, d = Math.hypot(dx, dy);
      if (b.state === "idle" && d > 30) {
        const ny = Phaser.Math.Clamp(spr.y + dy / d * 14 * dt, ARENA.top, ARENA.bot);
        spr.setPosition(Phaser.Math.Clamp(spr.x + dx / d * 14 * dt, ARENA.xl(ny), ARENA.xr(ny)), ny);
      }
    }
    if (Math.abs(spr.x - p.x) < 12 && Math.abs(spr.y - p.y) < 7 && b.state !== "stun" && b.state !== "hurt") this.hurtPlayer();

    // rats scurry at you
    for (const r of [...this.rats]) {
      r.life -= dt;
      const dx = p.x - r.x, dy = p.y - r.y, d = Math.hypot(dx, dy) || 1;
      const sp = (angry ? 50 : 40) * dt;
      const ny = Phaser.Math.Clamp(r.y + dy / d * sp, ARENA.top, ARENA.bot);
      r.setPosition(Phaser.Math.Clamp(r.x + dx / d * sp, ARENA.xl(ny) - 6, ARENA.xr(ny) + 6), ny).setFlipX(dx > 0).setDepth(r.y);
      if (d < 7) { this.hurtPlayer(); this.killRat(r, false); continue; }
      if (r.life <= 0) this.killRat(r, false);
    }
    if (this.swingFx.visible) this.placeSwing();
  },

  spawnRat(x, y) {
    const r = this.add.sprite(x, y, "boss_rat", "run_0").setOrigin(0.5, 0.9);
    r.play("boss_rat_run"); r.life = rand(5, 7);
    this.rats.push(r);
  },

  killRat(r, splat = true) {
    this.rats.splice(this.rats.indexOf(r), 1);
    if (splat) { const s = this.add.image(r.x, r.y - 4, "boss_fx", "splat").setDepth(r.y - 2); this.tweens.add({ targets: s, alpha: 0, delay: 800, duration: 600, onComplete: () => s.destroy() }); snd.sfx("squeak"); }
    r.destroy();
  },

  hurtPlayer() {
    if (this.inv > 0 || this.over || this.boss.phase !== "fight") return;
    this.php--; this.inv = 1.1;
    this.hearts.forEach((h, i) => h.setAlpha(i < this.php ? 1 : 0.2));
    snd.sfx("strike"); this.cameras.main.shake(180, 0.01);
    this.cameras.main.flash(120, 200, 30, 40);
    if (this.php <= 0) { this.p.setAlpha(1); this.endBossFx(); this.fail("ratking"); }
  },

  // ---------------------------------------------------------------- the mop
  swing() {
    const b = this.boss;
    if (!b || b.phase !== "fight" || this.swingCd > 0) return;
    this.swingCd = 0.42;
    snd.sfx("swing");
    this.swingFx.setVisible(true).setFlipX(this.face === "left").play("boss_fx_swing", true);
    this.mop.setVisible(true);
    this.placeSwing();
    this.time.delayedCall(220, () => { this.swingFx.setVisible(false); this.mop.setVisible(false); });
    const hx = this.p.x + (this.face === "left" ? -14 : this.face === "right" ? 14 : 0);
    const hy = this.p.y - 8 + (this.face === "up" ? -8 : this.face === "down" ? 6 : 0);
    for (const r of [...this.rats]) if (Phaser.Math.Distance.Between(hx, hy, r.x, r.y - 4) < 20) this.killRat(r);
    const spr = b.spr;
    if (Phaser.Math.Distance.Between(hx, hy, spr.x, spr.y - 14) < 32) {
      if (b.state === "stun") this.hitBoss();
      else { snd.sfx("clang"); this.cameras.main.shake(60, 0.003); }
    }
  },

  placeSwing() {
    const dir = this.face === "left" ? -1 : 1;
    this.swingFx.setPosition(this.p.x + dir * 12, this.p.y - 20);
    this.mop.setPosition(this.p.x + dir * 8, this.p.y - 10).setAngle(dir * 50).setFlipX(dir < 0);
  },

  hitBoss() {
    const b = this.boss, spr = b.spr;
    b.hp--; b.state = "hurt"; b.st = 0.22;
    spr.setFrame("hurt");
    this.bossBar.width = 108 * Math.max(0, b.hp) / BOSS_HP;
    const fx = this.add.sprite(spr.x, spr.y - 20, "boss_fx", "hit").setDepth(629);
    this.tweens.add({ targets: fx, scale: 1.6, alpha: 0, duration: 260, onComplete: () => fx.destroy() });
    snd.sfx("hitboss"); this.cameras.main.shake(120, 0.008);
    // knock it back
    const dir = Math.sign(spr.x - this.p.x) || 1;
    const nx = Phaser.Math.Clamp(spr.x + dir * 14, ARENA.xl(spr.y), ARENA.xr(spr.y));
    this.tweens.add({ targets: spr, x: nx, duration: 120 });
    if (b.hp <= 0) this.winBoss();
  },

  /** Tap during the fight: walk at the nearest enemy and swing when close. */
  fightTap(x, y) {
    const b = this.boss;
    if (!b || b.phase !== "fight") return;
    const enemies = [...this.rats, b.spr];
    let near = null, nd = 1e9;
    for (const e of enemies) { const d = Phaser.Math.Distance.Between(x, y, e.x, e.y - 8); if (d < nd) { nd = d; near = e; } }
    if (near && nd < 30) {
      const close = Phaser.Math.Distance.Between(this.p.x, this.p.y, near.x, near.y) < 26;
      this.face = near.x < this.p.x ? "left" : "right";
      if (close) return this.swing();
      this.target = { x: Phaser.Math.Clamp(near.x + (near.x < this.p.x ? 16 : -16), ARENA.xl(this.p.y), ARENA.xr(this.p.y)), y: Phaser.Math.Clamp(near.y, ARENA.top, ARENA.bot) };
      this.fightChase = near;
      return;
    }
    const ty = Phaser.Math.Clamp(y, ARENA.top, ARENA.bot);
    this.target = { x: Phaser.Math.Clamp(x, ARENA.xl(ty), ARENA.xr(ty)), y: ty };
    this.fightChase = null;
  },

  /** Called each frame in the fight: swing automatically when a tapped enemy comes into reach. */
  tickFightChase() {
    const e = this.fightChase;
    if (!e || !e.active) { this.fightChase = null; return; }
    if (Phaser.Math.Distance.Between(this.p.x, this.p.y, e.x, e.y) < 26) {
      this.face = e.x < this.p.x ? "left" : "right";
      this.target = null; this.fightChase = null; this.swing();
    }
  },

  endBossFx() {
    this.lineG?.clear(); this.stars?.setVisible(false); this.swingFx?.setVisible(false); this.mop?.setVisible(false);
  },

  winBoss() {
    const b = this.boss, spr = b.spr;
    b.phase = "won";
    this.endBossFx(); this.unhint("fight");
    snd.music("off"); snd.sfx("roar"); this.cameras.main.flash(400, 255, 255, 255);
    spr.play("boss_ratking_die");
    // it comes apart into rats that pour out of the door
    for (let i = 0; i < 14; i++) {
      const r = this.add.sprite(spr.x + rand(-26, 26), spr.y + rand(-6, 4), "boss_rat", "run_0").setOrigin(0.5, 0.9).setDepth(spr.y + 1);
      r.play("boss_rat_run"); r.setFlipX(r.x < 161);
      this.tweens.add({ targets: r, x: 161 + rand(-6, 6), y: 117, duration: rand(700, 1300), delay: i * 60, onComplete: () => r.destroy() });
    }
    for (const r of [...this.rats]) this.killRat(r);
    this.tweens.add({ targets: [spr, spr.sh], alpha: 0, delay: 600, duration: 700 });
    // all that's left of 덕구: his cap
    this.time.delayedCall(900, () => {
      this.add.image(spr.x, spr.y - 2, "boss_ratking", "idle_0").setCrop(18, 8, 36, 16).setDepth(spr.y - 1).setScale(1);
      this.say(t("dgGone"), 3);
      this.dgBubble.setPosition(spr.x, spr.y - 40);
    });
    const hazard = 30000;
    this.time.delayedCall(1600, () => {
      this.earn(hazard, this.p.x, this.p.y - 50);
      const m = txt(this, W / 2, 60, t("hazard") + " +₩30,000", { ox: 0.5, color: C.yellow, depth: 960 });
      this.tweens.add({ targets: m, alpha: 0, delay: 1500, duration: 400, onComplete: () => m.destroy() });
    });
    [this.fightPlate, this.hearts, this.bossBarBg, this.bossBar, this.bossName].flat().forEach(o => this.tweens.add({ targets: o, alpha: 0, delay: 1000, duration: 400 }));
    this.time.delayedCall(3400, () => { b.phase = "done"; this.p.setAlpha(1); this.min = 59; this.minT = 99; });
  },
};
