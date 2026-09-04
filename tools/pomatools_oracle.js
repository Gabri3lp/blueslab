/**
 * PoMaTools Oracle (tools/pomatools_oracle.js)
 * 
 * Reconstructed reference implementation of the Pokémon Masters EX damage calculation engine
 * extracted directly from pomatools.site (calcDamage in sync-damage.component).
 * 
 * Used for differential testing against BluesLab calculation logic.
 */

const DAMAGE_ROLLS = [
  // Non-Critical rolls (0.90 to 1.00)
  [
    0.899999976158142,
    0.910000026226043,
    0.9200000166893,
    0.930000007152557,
    0.939999997615814,
    0.949999988079071,
    0.959999978542327,
    0.970000028610229,
    0.980000019073486,
    0.990000009536743,
    1.0
  ],
  // Critical rolls (1.35 to 1.50)
  [
    1.3499999046325684,
    1.3650000095367432,
    1.3799999952316284,
    1.3949999809265137,
    1.409999966621399,
    1.4249999523162842,
    1.4399999380111694,
    1.4550000429153442,
    1.4700000286102295,
    1.4850000143051147,
    1.5
  ]
];

function calculatePoMaToolsDamage(options = {}) {
  const basePower = options.basePower ?? 100;
  const powerGrid = options.powerGrid ?? 0;
  const kind = options.kind ?? (options.isMax ? "MX" : (options.isSync ? "SN" : "MV"));
  const category = options.category ?? "Physical";
  const attackerStat = options.attackerStat ?? 500;
  const defenderStat = options.defenderStat ?? 200;
  const isCritical = options.isCritical ?? false;

  const passivePowerups = options.passivePercentage ?? options.passivePowerups ?? 0;
  const masterSkillBoost = options.masterPercentage ?? options.masterSkillBoost ?? 0;
  const pmun = options.pmun ?? 0;
  const smun = options.smun ?? 0;
  const syun = options.syun ?? 0;
  const innateScalingMultiplier1000 = options.innateModifier1000 ?? options.innateScalingMultiplier1000 ?? 1000;

  const weatherBoost = options.weatherBoost ?? false;
  const weatherEx = options.weatherEx ?? false;
  const terrainBoost = options.terrainBoost ?? false;
  const terrainEx = options.terrainEx ?? false;
  const zoneBoost = options.zoneBoost ?? false;
  const zoneEx = options.zoneEx ?? false;

  const effectiveness = options.isSuperEffective ?? options.effectiveness ?? false;
  const effectiveNext = options.superEffectiveNext ?? options.effectiveNext ?? false;
  const unity = options.unity ?? false;
  const cheer = options.cheer ?? false;
  const syncBoosts = options.syncBoosts ?? 0;

  const targets = options.targetCount ?? options.targets ?? 1;
  const isAoEMove = options.isAoEMove ?? (targets > 1);
  const noAoE = options.hasAoENoDecay ?? options.noAoE ?? false;

  const typeRebuff = options.typeRebuff ?? 0;

  const circlePhysAllies = options.circlePhysAllies ?? 0;
  const circleSpecAllies = options.circleSpecAllies ?? 0;
  const enemyCircleDefAllies = options.enemyCircleDefAllies ?? 0;

  const physicalBreak = options.physicalBreak ?? false;
  const specialBreak = options.specialBreak ?? false;

  const physicalScreen = options.physicalScreen ?? false;
  const specialScreen = options.specialScreen ?? false;

  const teraBoost = options.teraBoost ?? false;
  const stellarBoost = options.stellarBoost ?? false;

  const isPhys = (category === "Physical" || category === "CATE_001");
  const isSpec = !isPhys;

  // 1. Power-up percentage
  let me = 100 + passivePowerups;

  // Master passives do NOT affect Max moves ("MX"!==z.kind)
  if (kind !== "MX") {
    me += masterSkillBoost;
  }

  // Move kind specific boosts
  if (kind === "MV") {
    if (isPhys && pmun > 0) me += pmun * 40;
    if (isSpec && smun > 0) me += smun * 40;
  } else if (kind === "SN") {
    if (syun > 0) me += syun * 10;
  }

  const effectiveBasePower = basePower + powerGrid;
  const battlePower = Math.floor(Math.floor(effectiveBasePower * me / 100) * innateScalingMultiplier1000 / 1000);

  // 2. Fractional Multipliers Product (ne / he)
  let ne = 1;
  let he = 1;

  if (weatherBoost) {
    ne *= 3;
    he *= weatherEx ? 1 : 2;
  }
  if (terrainBoost) {
    ne *= 3;
    he *= terrainEx ? 1 : 2;
  }
  if (zoneBoost) {
    ne *= 3;
    he *= zoneEx ? 1 : 2;
  }

  // Tera (applies only to regular moves)
  if (kind === "MV") {
    if (stellarBoost) {
      ne *= 2;
    } else if (teraBoost) {
      ne *= 3;
      he *= 2;
    }
  }

  // Type effectiveness
  if (effectiveness) {
    ne *= effectiveNext ? 3 : 2;
  }

  if (unity) {
    ne *= 6;
    he *= 5;
  }
  if (cheer) {
    ne *= 3;
    he *= 2;
  }

  if (syncBoosts > 0) {
    ne *= (2 + syncBoosts);
    he *= 2;
  }

  // AoE Multi-target reduction: only for regular moves
  if (targets > 1 && isAoEMove && kind !== "SN" && kind !== "MX" && !noAoE) {
    if (targets === 3) {
      he *= 2;
    } else if (targets === 2) {
      ne *= 3333;
      he *= 5000;
    }
  }

  // Type Rebuffs
  switch (typeRebuff) {
    case -3: ne *= 8; he *= 5; break;
    case -2: ne *= 3; he *= 2; break;
    case -1: ne *= 13; he *= 10; break;
    case 1: ne *= 10; he *= 13; break;
    case 2: ne *= 3333; he *= 5000; break;
    case 3: ne *= 5; he *= 8; break;
  }

  // Regional Circles: apply to MV and SN, NOT MX
  if (kind === "MV" || kind === "SN") {
    if (isPhys && circlePhysAllies > 0) {
      ne *= (110 + 10 * circlePhysAllies);
      he *= 100;
    }
    if (isSpec && circleSpecAllies > 0) {
      ne *= (110 + 10 * circleSpecAllies);
      he *= 100;
    }
    if (enemyCircleDefAllies > 0) {
      ne *= (100 - (10 + 3 * enemyCircleDefAllies));
      he *= 100;
    }
  }

  // Breaks on target: apply ONLY to regular moves ("MV"===z.kind)
  if (kind === "MV") {
    if (isPhys && physicalBreak) {
      ne *= 3;
      he *= 2;
    }
    if (isSpec && specialBreak) {
      ne *= 3;
      he *= 2;
    }
  }

  // Damage Reduction screens: apply ONLY to regular moves and critical hits bypass them
  if (!isCritical && kind === "MV") {
    if (isPhys && physicalScreen) {
      ne *= 2;
      he *= 3;
    }
    if (isSpec && specialScreen) {
      ne *= 2;
      he *= 3;
    }
  }

  // Final roll calculations
  ne *= attackerStat;
  he *= defenderStat * 2;

  const critIdx = isCritical ? 1 : 0;
  const factor = Math.fround(battlePower * ne / he);
  const rolls = [];

  for (let l = 0; l < 10; ++l) {
    rolls.push(Math.floor(Math.fround(DAMAGE_ROLLS[critIdx][l] * factor)));
  }
  rolls.push(Math.floor(DAMAGE_ROLLS[critIdx][10] * battlePower * ne / he));

  return {
    battlePower,
    ne,
    he,
    rolls,
    min: rolls[0],
    max: rolls[10],
    avg: Math.round(rolls.reduce((a, b) => a + b, 0) / rolls.length)
  };
}

module.exports = {
  DAMAGE_ROLLS,
  calculatePoMaToolsDamage
};
