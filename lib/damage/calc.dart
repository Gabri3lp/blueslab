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

const _speedVariation = <int, double>{
  -6: 0.38, -5: 0.41, -4: 0.45, -3: 0.50, -2: 0.55, -1: 0.66,
  0: 1.00,
  1: 1.50, 2: 1.80, 3: 2.00, 4: 2.20, 5: 2.40, 6: 2.60,
};

double statVariation(int stage, {bool isSpeed = false}) =>
    (isSpeed ? _speedVariation : _atkDefVariation)[stage.clamp(-6, 6)] ?? 1.0;

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
  final double skillIncrease; // Skill stat multiplier (e.g. 1.1 for 10%)
  final bool isSpeed;

  const StatInput({
    required this.baseStat,
    this.gridStat = 0,
    this.gear = 0,
    this.themeStat = 0,
    this.stage = 0,
    this.isBurned = false,
    this.lessenBurn = 0,
    this.mitigation = 0,
    this.skillIncrease = 1.0,
    this.isSpeed = false,
  });
}

enum CircleType { physical, special, defensive }

/// A single Circle field effect active on the allied field.
/// [allyCount] = extra allies with the matching region theme (0-3).
///
/// Physical/Special circles:
///   Power-up: 10% base + 10% per extra ally (max 40%).
///   DR: 5% base + 3% per extra ally (max 14%).
///
/// Defensive circles:
///   Power-up: 5% base + 5% per extra ally (max 20%).
///   DR: 10% base + 5% per extra ally (max 25%).
class CircleEffect {
  final CircleType type;
  final int allyCount;

  const CircleEffect({required this.type, this.allyCount = 0});

  double get powerUp {
    final n = allyCount.clamp(0, 3);
    if (type == CircleType.defensive) {
      return 1 + (5 + n * 5) / 100;
    }
    return 1 + (10 + n * 10) / 100;
  }

  double get damageReduction {
    final n = allyCount.clamp(0, 3);
    if (type == CircleType.defensive) {
      return 1 - (10 + n * 5) / 100;
    }
    return 1 - (5 + n * 3) / 100;
  }
}

class BattleConditions {
  final int syncBoosts;       // 0+
  final bool isCritical;
  final bool isSuperEffective;
  final bool hasSENext;       // Super Effective ↑ Next (x3 instead of x2)
  final int targetCount;      // 1, 2, or 3
  final bool zoneBoost;
  final bool zoneEx;
  final bool terrainBoost;
  final bool terrainEx;
  final bool weatherBoost;
  final bool weatherEx;
  final bool unityBonus;
  final int typeRebuff;       // -3 to 0, per move type
  final int stellarRebuff;    // -3 to 0, only for Stellar moves
  final bool physicalBreak;   // ×1.5 for physical moves
  final bool specialBreak;    // ×1.5 for special moves
  final bool isPhysicalMove;  // true = physical, false = special
  final List<CircleEffect> circles; // active circles on allied field

  const BattleConditions({
    this.syncBoosts = 0,
    this.isCritical = false,
    this.isSuperEffective = false,
    this.hasSENext = false,
    this.targetCount = 1,
    this.zoneBoost = false,
    this.zoneEx = false,
    this.terrainBoost = false,
    this.terrainEx = false,
    this.weatherBoost = false,
    this.weatherEx = false,
    this.unityBonus = false,
    this.typeRebuff = 0,
    this.stellarRebuff = 0,
    this.physicalBreak = false,
    this.specialBreak = false,
    this.isPhysicalMove = true,
    this.circles = const [],
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
  var formStat = input.baseStat + input.gear + input.themeStat;

  // Skill Increase applies to form stat before grid
  if (input.skillIncrease != 1.0) {
    formStat = (formStat * input.skillIncrease).ceil() - 1;
  }

  final base = formStat + input.gridStat;

  if (critDefense && input.stage > 0) {
    return floorToInt(base * 1.0);
  }

  var variation = statVariation(input.stage, isSpeed: input.isSpeed);

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

/// Offensive circle multiplier. Physical circles boost physical moves,
/// Special circles boost special moves, Defensive circles boost all moves.
/// Multiple circles multiply together.
double calcCircleOffenseMult(List<CircleEffect> circles, bool isPhysical) {
  var product = 1.0;
  for (final c in circles) {
    if (c.type == CircleType.defensive ||
        (isPhysical && c.type == CircleType.physical) ||
        (!isPhysical && c.type == CircleType.special)) {
      product *= c.powerUp;
    }
  }
  return product;
}

/// Defensive circle multiplier: Physical circles reduce physical damage,
/// Special circles reduce special damage, Defensive circles reduce all damage.
/// Multiple circles multiply together.
double calcCircleDefenseMult(List<CircleEffect> circles, bool isPhysical) {
  var product = 1.0;
  for (final c in circles) {
    if (c.type == CircleType.defensive ||
        (isPhysical && c.type == CircleType.physical) ||
        (!isPhysical && c.type == CircleType.special)) {
      product *= c.damageReduction;
    }
  }
  return product;
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

  if (bc.zoneBoost) mult *= bc.zoneEx ? 3.0 : 1.5;
  if (bc.terrainBoost) mult *= bc.terrainEx ? 3.0 : 1.5;
  if (bc.weatherBoost) mult *= bc.weatherEx ? 3.0 : 1.5;
  if (bc.unityBonus) mult *= 1.2;
  if (bc.physicalBreak) mult *= 1.5;
  if (bc.specialBreak) mult *= 1.5;

  // Circles: multiply between each other, then applied as field boost
  if (bc.circles.isNotEmpty) {
    mult *= calcCircleOffenseMult(bc.circles, bc.isPhysicalMove);
  }

  // Type Rebuff (Table 25)
  const rebuffMultipliers = <int, double>{
    -3: 1.6, -2: 1.5, -1: 1.3,
  };
  if (bc.typeRebuff != 0 && rebuffMultipliers.containsKey(bc.typeRebuff)) {
    mult *= rebuffMultipliers[bc.typeRebuff]!;
  }
  if (bc.stellarRebuff != 0 && rebuffMultipliers.containsKey(bc.stellarRebuff)) {
    mult *= rebuffMultipliers[bc.stellarRebuff]!;
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
