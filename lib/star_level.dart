// Star level potential bonus calculations

/// Returns the potential stat bonus for a given star configuration.
/// [baseRarity] is the original rarity of the pair (3, 4, or 5).
/// [targetStars] is the selected star level: e.g. '4★', '5★', '5★ 20/20'.
/// [isEx] adds the EX base bonus (+100 HP, +40 rest).
/// [exRole] adds the EX Role bonus if non-empty.
Map<String, int> calcPotentialBonus({
  required int baseRarity,
  required String targetStars,
}) {
  // For 5★ base pairs: JSON stats already include 20/20 potential.
  //   5★ / 5★ 20/20 / 5★ EX: no extra potential needed.
  // For 3★/4★ base pairs: JSON stats are at base rarity, 0 potential.
  //   Each star promotion = 20 potentials (HP+2, rest+1 each).
  //   20/20 or EX = one more star worth of potentials.
  if (baseRarity >= 5) {
    if (targetStars == '5★') {
      return {'hp': 0, 'atk': 0, 'def': 0, 'spa': 0, 'spd': 0, 'spe': 0};
    }
    // 5★ 20/20 or EX: 20 potentials at 5★ rate (HP+5, rest+2)
    return {'hp': 100, 'atk': 40, 'def': 40, 'spa': 40, 'spd': 40, 'spe': 40};
  }

  int starsGained = 0;
  if (targetStars.contains('EX') || targetStars.contains('20/20')) {
    starsGained = 5 - baseRarity + 1; // +1 for the 20/20 tier
  } else {
    final match = RegExp(r'(\d)').firstMatch(targetStars);
    final target = match != null ? int.parse(match.group(1)!) : baseRarity;
    starsGained = target - baseRarity;
  }

  if (starsGained <= 0) {
    return {'hp': 0, 'atk': 0, 'def': 0, 'spa': 0, 'spd': 0, 'spe': 0};
  }

  final potentials = starsGained * 20;
  final hpBonus = potentials * 2;
  final restBonus = potentials * 1;

  return {
    'hp': hpBonus,
    'atk': restBonus,
    'def': restBonus,
    'spa': restBonus,
    'spd': restBonus,
    'spe': restBonus,
  };
}

/// Returns the list of available star levels for a pair.
List<String> availableStarLevels(int baseRarity, bool hasEx) {
  final levels = <String>[];
  for (int s = baseRarity; s <= 4; s++) {
    levels.add('$s★');
  }
  levels.add('5★');
  if (hasEx) {
    levels.add('5★ EX');
  } else {
    levels.add('5★ 20/20');
  }
  return levels;
}

/// Default star level for a pair.
String defaultStarLevel(bool hasEx) => '5★ 20/20';

const exBaseBonus = <String, int>{};

const exRoleBonusMap = <String, Map<String, int>>{
  'Strike': {'hp': 60, 'atk': 40, 'spa': 40},
  'Tech': {'hp': 60, 'def': 20, 'spa': 20, 'spd': 20},
  'Support': {'hp': 60, 'def': 40, 'spd': 40},
  'Sprint': {'hp': 60, 'atk': 20, 'spa': 20, 'spe': 40},
  'Field': {'hp': 60, 'def': 20, 'spd': 20, 'spe': 40},
  'Multi': {'hp': 60, 'atk': 20, 'def': 20, 'spa': 20, 'spd': 20, 'spe': 20},
};

/// Super Awakening stat multiplier at SA level 1+ (×1.1 for all stats, all roles).
double saStatMultiplier(int saLevel) => saLevel >= 1 ? 1.1 : 1.0;

/// Super Awakening flat stat bonuses for Support at SA levels 2-4.
Map<String, int> saSupportFlatBonus(int saLevel) {
  int hp = 0, def = 0, spd = 0;
  if (saLevel >= 2) hp += 50;
  if (saLevel >= 3) { def += 20; spd += 20; }
  if (saLevel >= 4) hp += 100;
  return {'hp': hp, 'def': def, 'spd': spd};
}

/// Super Awakening extra percentage added to the Move Level multiplier.
/// Returns the extra percentage points (e.g. 10 for +10%, 20 for +20%).
int saMovePowerBonus(int saLevel, String role, {required bool isSync}) {
  final r = role.toLowerCase().trim();
  final isStrikeSprint = r.startsWith('strike') || r.startsWith('sprint');
  final isTechField = r.startsWith('tech') || r.startsWith('field');
  if (isStrikeSprint) {
    if (!isSync) {
      if (saLevel >= 4) return 30;
      if (saLevel >= 2) return 10;
    } else {
      if (saLevel >= 3) return 20;
    }
  } else if (isTechField) {
    if (isSync) {
      if (saLevel >= 4) return 40;
      if (saLevel >= 2) return 10;
    } else {
      if (saLevel >= 3) return 20;
    }
  }
  return 0;
}
