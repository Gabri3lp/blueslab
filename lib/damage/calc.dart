import 'dart:math' as math;

// --- Rounding helpers matching the document notation ---
int floorToInt(double v) => v.floor(); // 0< > round down
int ceilToInt(double v) => v.ceil();   // 0〈 〉 round up
double roundTo(int decimals, double v) {
  final f = math.pow(10, decimals);
  return (v * f).roundToDouble() / f;
}
double floorTo(int decimals, double v) {
  final f = math.pow(10, decimals);
  return (v * f).floorToDouble() / f;
}
double ceilTo(int decimals, double v) {
  final f = math.pow(10, decimals);
  return (v * f).ceilToDouble() / f;
}

// --- Stat stage tables (Table 21) ---
const _atkDefVariation = <int, double>{
  -6: 0.55, -5: 0.58, -4: 0.62, -3: 0.66, -2: 0.71, -1: 0.80,
  0: 1.00,
  1: 1.25, 2: 1.40, 3: 1.50, 4: 1.60, 5: 1.70, 6: 1.80,
};

double statVariation(int stage) =>
    _atkDefVariation[stage.clamp(-6, 6)] ?? 1.0;

// --- Data classes ---

class MovePowerInput {
  final int basePower;
  final int moveLevel;       // 1-5
  final int gridPower;       // sum of green tiles
  final double skillPowerUps; // ΣSkillPowerUps
  final int boostRank;       // Physical/Special Move ↑ Next (0-10)
  final double modifier;     // move-specific modifier (default 1)
  final double increment;    // 6EX Tech sync = 1.5, Hit the Gas, etc. (default 1)

  const MovePowerInput({
    required this.basePower,
    this.moveLevel = 5,
    this.gridPower = 0,
    this.skillPowerUps = 0,
    this.boostRank = 0,
    this.modifier = 1,
    this.increment = 1,
  });
}

class StatInput {
  final int baseStat;
  final int gridStat;
  final int gear;
  final int themeStat;
  final int stage;      // -6 to +6
  final bool isBurned;
  final int lessenBurn; // 0-9
  final int mitigation; // 0-9 (Stout Heart, Trained Body, etc.)

  const StatInput({
    required this.baseStat,
    this.gridStat = 0,
    this.gear = 0,
    this.themeStat = 0,
    this.stage = 0,
    this.isBurned = false,
    this.lessenBurn = 0,
    this.mitigation = 0,
  });
}

class BattleConditions {
  final int syncBoosts;       // 0+
  final bool isCritical;
  final bool isSuperEffective;
  final bool hasSENext;       // Super Effective ↑ Next (x3 instead of x2)
  final int targetCount;      // 1, 2, or 3
  final bool weatherBoost;    // weather/terrain/zone matching
  final bool hasScreen;       // physical/special reduction screen
  final bool isLegendaryArena; // affects screen multiplier
  final bool unityBonus;

  const BattleConditions({
    this.syncBoosts = 0,
    this.isCritical = false,
    this.isSuperEffective = false,
    this.hasSENext = false,
    this.targetCount = 1,
    this.weatherBoost = false,
    this.hasScreen = false,
    this.isLegendaryArena = false,
    this.unityBonus = false,
  });
}

class DamageResult {
  final int movePower;
  final int attackerStat;
  final int defenderStat;
  final double statRatio;
  final double battleMult;
  final List<int> rolls;

  const DamageResult({
    required this.movePower,
    required this.attackerStat,
    required this.defenderStat,
    required this.statRatio,
    required this.battleMult,
    required this.rolls,
  });
}

// --- Calculation functions ---

/// Power(Base, Level) = 0<0<Base × (100 + (Level-1)×5) / 100> × Increment>
int calcPower(int base, int level, double increment) {
  final scaled = floorToInt(base * (100 + (level - 1) * 5) / 100);
  return floorToInt(scaled * increment);
}

/// Move Power = 0<0<(Power + Grid) × (1 + ΣSkillPowerUps + Boosts)> × Modifier>
int calcMovePower(MovePowerInput input) {
  final power = calcPower(input.basePower, input.moveLevel, input.increment);
  final boost = input.boostRank * 0.4;
  final inner = floorToInt((power + input.gridPower) * (1 + input.skillPowerUps + boost));
  return floorToInt(inner * input.modifier);
}

/// Stat = 0<(FormStat + Grid + Gear + Theme) × Variation>
int calcStat(StatInput input, {bool critOffense = false, bool critDefense = false}) {
  final base = input.baseStat + input.gridStat + input.gear + input.themeStat;

  if (critDefense && input.stage > 0) {
    // Crit ignores raised defense
    return floorToInt(base * 1.0);
  }

  var variation = statVariation(input.stage);

  // Apply mitigation for negative stages
  if (input.stage < 0 && input.mitigation > 0) {
    final mit = input.mitigation * 0.1;
    variation = 1 - (1 - variation) * (1 - mit);
  }

  if (input.isBurned) {
    final mitigation = input.lessenBurn * 0.1;
    final burnVariation = 1 - 0.2 * (1 - mitigation);
    variation *= burnVariation;
  }

  final calculated = floorToInt(base * variation);

  if (critOffense && input.stage < 0) {
    // Crit: use max between calculated and base without variation/theme
    final raw = input.baseStat + input.gridStat + input.gear;
    return math.max(calculated, raw);
  }

  return calculated;
}

/// Battle Conditions multiplier
double calcBattleMultiplier(BattleConditions bc) {
  var mult = 1.0;

  if (bc.syncBoosts > 0) mult *= 1 + bc.syncBoosts * 0.5;
  if (bc.isCritical) mult *= 1.5;
  if (bc.isSuperEffective) mult *= bc.hasSENext ? 3.0 : 2.0;

  switch (bc.targetCount) {
    case 2: mult *= 0.6666; break;
    case 3: mult *= 0.5; break;
  }

  if (bc.weatherBoost) mult *= 1.5;
  if (bc.unityBonus) mult *= 1.2;

  if (bc.hasScreen) {
    mult *= bc.isLegendaryArena ? 0.5 : 0.6666;
  }

  return mult;
}

/// Full damage calculation
DamageResult calcDamage({
  required MovePowerInput moveInput,
  required StatInput attackerInput,
  required int defenderStat,
  required BattleConditions conditions,
}) {
  final movePower = calcMovePower(moveInput);
  final atkStat = calcStat(
    attackerInput,
    critOffense: conditions.isCritical,
  );
  final statRatio = atkStat * 0.5 / defenderStat;
  final battleMult = calcBattleMultiplier(conditions);

  const damageRolls = [0.90, 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99, 1.00];
  final baseDmg = movePower * statRatio * battleMult;
  final rolls = damageRolls.map((r) => floorToInt(baseDmg * r)).toList();

  return DamageResult(
    movePower: movePower,
    attackerStat: atkStat,
    defenderStat: defenderStat,
    statRatio: statRatio,
    battleMult: battleMult,
    rolls: rolls,
  );
}
