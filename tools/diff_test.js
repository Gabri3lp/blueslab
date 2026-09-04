/**
 * Differential Testing Suite (tools/diff_test.js)
 * 
 * Verifies calculation and scope fidelity between BluesLab and PoMaTools Oracle.
 * Ensures that rule discrepancies (e.g. Max moves receiving breaks or screens,
 * in-battle modifiers improperly applied) can never slip through.
 */

const fs = require('fs');
const path = require('path');
const { calculatePoMaToolsDamage, DAMAGE_ROLLS } = require('./pomatools_oracle');

const DATA_DIR = path.join(__dirname, '..', 'src', 'BluesLab', 'wwwroot', 'data');
const PAIRS_DIR = path.join(DATA_DIR, 'pairs');

/**
 * BluesLab calculation simulator mirroring C# DamageCalculatorService logic exactly.
 */
function calculateBluesLabDamage(options = {}) {
  const basePower = options.basePower ?? 100;
  const powerGrid = options.powerGrid ?? 0;
  const isSync = options.isSync ?? false;
  const isMax = options.isMax ?? false;
  const category = options.category ?? "Physical";
  const attackerStat = options.attackerStat ?? 500;
  const defenderStat = options.defenderStat ?? 200;
  const isCritical = options.isCritical ?? false;

  const passivePercentage = options.passivePercentage ?? options.passivePowerups ?? 0;
  const masterPercentage = options.masterPercentage ?? options.masterSkillBoost ?? 0;
  const pmun = options.pmun ?? 0;
  const smun = options.smun ?? 0;
  const syun = options.syun ?? 0;
  const innateModifier1000 = options.innateModifier1000 ?? options.innateScalingMultiplier1000 ?? 1000;

  const weatherBoost = options.weatherBoost ?? false;
  const weatherEx = options.weatherEx ?? false;
  const terrainBoost = options.terrainBoost ?? false;
  const terrainEx = options.terrainEx ?? false;
  const zoneBoost = options.zoneBoost ?? false;
  const zoneEx = options.zoneEx ?? false;

  const isSuperEffective = options.isSuperEffective ?? options.effectiveness ?? false;
  const superEffectiveNext = options.superEffectiveNext ?? options.effectiveNext ?? false;
  const unity = options.unity ?? false;
  const cheer = options.cheer ?? false;
  const syncBoosts = options.syncBoosts ?? 0;

  const targetCount = options.targetCount ?? options.targets ?? 1;
  const isAoEMove = options.isAoEMove ?? (targetCount > 1);
  const hasAoENoDecay = options.hasAoENoDecay ?? options.noAoE ?? false;

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

  // Mirroring MoveScopeRules:
  const isRegularMove = !isSync && !isMax;
  const isSyncMove = isSync && !isMax;
  const isMaxMove = isMax;

  const allowsBreaks = isRegularMove;
  const allowsScreens = isRegularMove;
  const allowsAoEPenalty = isRegularMove;
  const allowsCircles = !isMaxMove;
  const allowsMasterPassives = !isMaxMove;
  const allowsMoveBoostNext = isRegularMove;
  const allowsSyncBoostNext = isSync;
  const allowsTeraBoost = isRegularMove;

  const isPhysical = (category === "Physical" || category === "CATE_001");
  const isSpecial = !isPhysical;

  // 1. Battle Power
  let boostNextPercentage = 0;
  if (allowsMoveBoostNext) {
    if (isPhysical) boostNextPercentage += pmun * 40;
    if (isSpecial) boostNextPercentage += smun * 40;
  } else if (allowsSyncBoostNext) {
    boostNextPercentage += syun * 10;
  }

  const effectiveMasterPct = allowsMasterPassives ? masterPercentage : 0;
  const totalPowerupPercent = 100 + passivePercentage + effectiveMasterPct + boostNextPercentage;
  const baseMovePower = basePower + powerGrid;
  const battlePower = Math.floor(Math.floor(baseMovePower * totalPowerupPercent / 100) * innateModifier1000 / 1000);

  // 2. Fractional Multipliers (ne / he)
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

  if (allowsTeraBoost) {
    if (stellarBoost) {
      ne *= 2;
    } else if (teraBoost) {
      ne *= 3;
      he *= 2;
    }
  }

  if (isSuperEffective) {
    ne *= superEffectiveNext ? 3 : 2;
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

  if (targetCount > 1 && isAoEMove && allowsAoEPenalty && !hasAoENoDecay) {
    if (targetCount === 3) {
      he *= 2;
    } else if (targetCount === 2) {
      ne *= 3333;
      he *= 5000;
    }
  }

  switch (typeRebuff) {
    case -3: ne *= 8; he *= 5; break;
    case -2: ne *= 3; he *= 2; break;
    case -1: ne *= 13; he *= 10; break;
    case 1: ne *= 10; he *= 13; break;
    case 2: ne *= 3333; he *= 5000; break;
    case 3: ne *= 5; he *= 8; break;
  }

  if (allowsCircles) {
    if (isPhysical && circlePhysAllies > 0) {
      ne *= (110 + 10 * circlePhysAllies);
      he *= 100;
    }
    if (isSpecial && circleSpecAllies > 0) {
      ne *= (110 + 10 * circleSpecAllies);
      he *= 100;
    }
    if (enemyCircleDefAllies > 0) {
      ne *= (100 - (10 + 3 * enemyCircleDefAllies));
      he *= 100;
    }
  }

  if (allowsBreaks) {
    if (isPhysical && physicalBreak) {
      ne *= 3;
      he *= 2;
    }
    if (isSpecial && specialBreak) {
      ne *= 3;
      he *= 2;
    }
  }

  if (!isCritical && allowsScreens) {
    if (isPhysical && physicalScreen) {
      ne *= 2;
      he *= 3;
    }
    if (isSpecial && specialScreen) {
      ne *= 2;
      he *= 3;
    }
  }

  // 3. Rolls
  ne *= attackerStat;
  he *= defenderStat * 2;

  const rollIndex = isCritical ? 1 : 0;
  const baseFactor = Math.fround(battlePower * ne / he);
  const rolls = [];

  for (let l = 0; l < 10; l++) {
    rolls.push(Math.floor(Math.fround(DAMAGE_ROLLS[rollIndex][l] * baseFactor)));
  }
  rolls.push(Math.floor(DAMAGE_ROLLS[rollIndex][10] * battlePower * ne / he));

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

function runDifferentialTests() {
  console.log('='.repeat(70));
  console.log('   BLUESLAB vs POMATOOLS JS RUNTIME DIFFERENTIAL TEST SUITE');
  console.log('='.repeat(70));

  const startTime = Date.now();
  let totalScenarios = 0;
  let totalChecks = 0;
  let discrepancies = [];

  // =========================================================================
  // TEST SECTION 1: Exhaustive Scope Rules & Modifiers Combinatorial Matrix
  // =========================================================================
  console.log('\n[*] Ejecutando Matriz Combinatoria Exhaustiva de Reglas de Ámbito...');

  const moveKinds = [
    { kind: "MV", isSync: false, isMax: false, label: "Regular Move" },
    { kind: "SN", isSync: true,  isMax: false, label: "Sync Move" },
    { kind: "MX", isSync: false, isMax: true,  label: "Max Move" }
  ];

  const categories = ["Physical", "Special"];
  const crits = [false, true];
  const breaksList = [
    { phys: false, spec: false, label: "No Breaks" },
    { phys: true,  spec: false, label: "Physical Break" },
    { phys: false, spec: true,  label: "Special Break" }
  ];
  const screensList = [
    { phys: false, spec: false, label: "No Screens" },
    { phys: true,  spec: false, label: "Reflect Screen" },
    { phys: false, spec: true,  label: "Light Screen" }
  ];
  const circleOptions = [0, 1, 3];
  const masterPassives = [0, 20];
  const boostStacks = [0, 3, 10]; // PMUN / SMUN / SYUN
  const targetCounts = [1, 2, 3];
  const rebuffs = [-3, -1, 0, 1, 3];
  const wtzOptions = [
    { w: false, wex: false, t: false, tex: false, z: false, zex: false, label: "Clear" },
    { w: true,  wex: false, t: false, tex: false, z: false, zex: false, label: "Weather Standard" },
    { w: true,  wex: true,  t: false, tex: false, z: false, zex: false, label: "Weather EX" },
    { w: false, wex: false, t: true,  tex: true,  z: false, zex: false, label: "Terrain EX" },
    { w: false, wex: false, t: false, tex: false, z: true,  zex: false, label: "Zone Standard" }
  ];

  for (const mk of moveKinds) {
    for (const cat of categories) {
      for (const crit of crits) {
        for (const brk of breaksList) {
          for (const scr of screensList) {
            for (const circ of circleOptions) {
              for (const mp of masterPassives) {
                for (const stack of boostStacks) {
                  for (const tc of targetCounts) {
                    for (const rebuff of rebuffs) {
                      for (const wtz of wtzOptions) {
                        totalScenarios++;

                        const scenarioParams = {
                          basePower: 120,
                          powerGrid: 10,
                          category: cat,
                          attackerStat: 450,
                          defenderStat: 180,
                          isCritical: crit,
                          passivePercentage: 20,
                          passivePowerups: 20,
                          masterSkillBoost: mp,
                          masterPercentage: mp,
                          pmun: cat === "Physical" ? stack : 0,
                          smun: cat === "Special" ? stack : 0,
                          syun: stack,
                          innateScalingMultiplier1000: 1000,
                          innateModifier1000: 1000,

                          weatherBoost: wtz.w,
                          weatherEx: wtz.wex,
                          terrainBoost: wtz.t,
                          terrainEx: wtz.tex,
                          zoneBoost: wtz.z,
                          zoneEx: wtz.zex,

                          effectiveness: true,
                          isSuperEffective: true,
                          effectiveNext: false,
                          superEffectiveNext: false,
                          unity: false,
                          cheer: false,
                          syncBoosts: 1,

                          targets: tc,
                          targetCount: tc,
                          isAoEMove: tc > 1,
                          noAoE: false,
                          hasAoENoDecay: false,

                          typeRebuff: rebuff,

                          circlePhysAllies: cat === "Physical" ? circ : 0,
                          circleSpecAllies: cat === "Special" ? circ : 0,
                          enemyCircleDefAllies: 0,

                          physicalBreak: brk.phys,
                          specialBreak: brk.spec,

                          physicalScreen: scr.phys,
                          specialScreen: scr.spec
                        };

                        // PoMaTools Oracle call
                        const pomaResult = calculatePoMaToolsDamage({
                          ...scenarioParams,
                          kind: mk.kind
                        });

                        // BluesLab Calculator call
                        const bluesResult = calculateBluesLabDamage({
                          ...scenarioParams,
                          isSync: mk.isSync,
                          isMax: mk.isMax
                        });

                        // Check Battle Power
                        totalChecks++;
                        if (pomaResult.battlePower !== bluesResult.battlePower) {
                          discrepancies.push({
                            type: "BattlePower Mismatch",
                            scenario: `${mk.label} | ${cat} | Crit=${crit} | Breaks=${brk.label} | Screens=${scr.label}`,
                            expected: pomaResult.battlePower,
                            actual: bluesResult.battlePower
                          });
                        }

                        // Check Rolls [0..10]
                        for (let r = 0; r <= 10; r++) {
                          totalChecks++;
                          if (pomaResult.rolls[r] !== bluesResult.rolls[r]) {
                            discrepancies.push({
                              type: `Roll[${r}] Mismatch`,
                              scenario: `${mk.label} | ${cat} | Crit=${crit} | Breaks=${brk.label} | Screens=${scr.label}`,
                              expected: pomaResult.rolls[r],
                              actual: bluesResult.rolls[r]
                            });
                            break;
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }

  console.log(`[+] Matriz de Reglas ejecutada: ${totalScenarios.toLocaleString()} escenarios simulados.`);

  // =========================================================================
  // TEST SECTION 2: Real Sync Pair Dataset Audit
  // =========================================================================
  console.log('\n[*] Auditando Compis Reales con Movimientos Dinamax y Sincronizados...');

  if (fs.existsSync(PAIRS_DIR)) {
    const pairFiles = fs.readdirSync(PAIRS_DIR).filter(f => f.endsWith('.json'));
    let realPairsAudited = 0;
    let realMovesAudited = 0;

    for (const file of pairFiles) {
      const filePath = path.join(PAIRS_DIR, file);
      try {
        const pair = JSON.parse(fs.readFileSync(filePath, 'utf8'));
        realPairsAudited++;

        const isDynamax = (pair.maxMoves && pair.maxMoves.length > 0) ||
                          (pair.moves && pair.moves.some(m => m.isMax)) ||
                          (pair.dynamaxMoves && pair.dynamaxMoves.length > 0);

        const moves = pair.moves || [];
        for (const m of moves) {
          if (m.category === "Status") continue;
          const pwr = parseInt(m.power) || 0;
          if (pwr <= 0) continue;

          realMovesAudited++;
          const isSync = !!m.isSync;
          const isMax = !!m.isMax;
          const kind = isMax ? "MX" : (isSync ? "SN" : "MV");

          // Test real move under combat conditions (break + screen + circle + weather)
          const params = {
            basePower: pwr,
            powerGrid: 0,
            category: m.category || "Physical",
            attackerStat: 400,
            defenderStat: 150,
            isCritical: false,
            passivePercentage: 0,
            passivePowerups: 0,
            masterSkillBoost: 20,
            masterPercentage: 20,
            pmun: 2,
            smun: 2,
            syun: 2,
            innateScalingMultiplier1000: 1000,
            innateModifier1000: 1000,
            weatherBoost: true,
            weatherEx: false,
            terrainBoost: false,
            terrainEx: false,
            zoneBoost: false,
            zoneEx: false,
            effectiveness: false,
            isSuperEffective: false,
            effectiveNext: false,
            superEffectiveNext: false,
            unity: false,
            cheer: false,
            syncBoosts: 1,
            targets: 1,
            targetCount: 1,
            isAoEMove: false,
            noAoE: false,
            hasAoENoDecay: false,
            typeRebuff: 0,
            circlePhysAllies: 2,
            circleSpecAllies: 2,
            enemyCircleDefAllies: 0,
            physicalBreak: true,
            specialBreak: true,
            physicalScreen: true,
            specialScreen: true
          };

          const poma = calculatePoMaToolsDamage({ ...params, kind });
          const blues = calculateBluesLabDamage({ ...params, isSync, isMax });

          totalChecks++;
          if (poma.battlePower !== blues.battlePower) {
            discrepancies.push({
              type: `Real Pair Move BP Mismatch (${pair.displayName} - ${m.name})`,
              scenario: `Kind=${kind}`,
              expected: poma.battlePower,
              actual: blues.battlePower
            });
          }

          for (let r = 0; r <= 10; r++) {
            totalChecks++;
            if (poma.rolls[r] !== blues.rolls[r]) {
              discrepancies.push({
                type: `Real Pair Move Roll[${r}] Mismatch (${pair.displayName} - ${m.name})`,
                scenario: `Kind=${kind}`,
                expected: poma.rolls[r],
                actual: blues.rolls[r]
              });
              break;
            }
          }

          // If Dynamax pair, also audit the generated Max Move version
          if (isDynamax && !isSync && !isMax) {
            const maxParams = { ...params, basePower: 400 };
            const pomaMax = calculatePoMaToolsDamage({ ...maxParams, kind: "MX" });
            const bluesMax = calculateBluesLabDamage({ ...maxParams, isSync: false, isMax: true });

            totalChecks++;
            if (pomaMax.battlePower !== bluesMax.battlePower) {
              discrepancies.push({
                type: `Max Move BP Mismatch (${pair.displayName} - Max ${m.name})`,
                scenario: "Kind=MX",
                expected: pomaMax.battlePower,
                actual: bluesMax.battlePower
              });
            }

            for (let r = 0; r <= 10; r++) {
              totalChecks++;
              if (pomaMax.rolls[r] !== bluesMax.rolls[r]) {
                discrepancies.push({
                  type: `Max Move Roll[${r}] Mismatch (${pair.displayName} - Max ${m.name})`,
                  scenario: "Kind=MX",
                  expected: pomaMax.rolls[r],
                  actual: bluesMax.rolls[r]
                });
                break;
              }
            }
          }
        }
      } catch (err) {
        // Continue
      }
    }

    console.log(`[+] Compis auditados: ${realPairsAudited}`);
    console.log(`[+] Movimientos de compis auditados: ${realMovesAudited}`);
  }

  const durationMs = Date.now() - startTime;
  const fidelity = totalChecks > 0 ? ((totalChecks - discrepancies.length) / totalChecks * 100.0) : 0;

  console.log('\n' + '-'.repeat(70));
  console.log(`[+] Tiempo de ejecución:               ${durationMs} ms`);
  console.log(`[+] Total de verificaciones de daño:   ${totalChecks.toLocaleString()}`);
  console.log(`[+] Discrepancias encontradas:         ${discrepancies.length}`);
  console.log(`[+] FIDELIDAD DIFERENCIAL POMATOOLS:   ${fidelity.toFixed(2)}%`);
  console.log('-'.repeat(70));

  if (discrepancies.length > 0) {
    console.error(`\n[!] ERROR: Se detectaron ${discrepancies.length} discrepancias en el motor.`);
    for (const d of discrepancies.slice(0, 10)) {
      console.error(`  - ${d.type} | ${d.scenario} | Expected=${d.expected} Actual=${d.actual}`);
    }
    process.exit(1);
  } else {
    console.log('\n[OK] ¡100.00% de coincidencia exacta con el Oracle de PoMaTools!');
    process.exit(0);
  }
}

if (require.main === module) {
  runDifferentialTests();
}

module.exports = {
  calculateBluesLabDamage,
  runDifferentialTests
};
