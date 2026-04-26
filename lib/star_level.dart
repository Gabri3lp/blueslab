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
  int hpBonus = 0, restBonus = 0;

  if (baseRarity <= 3) {
    if (targetStars == '4★') {
      hpBonus = 20 * 2; restBonus = 20 * 1; // 3→4
    } else if (targetStars == '5★') {
      hpBonus = 40 * 2; restBonus = 40 * 1; // 3→4→5
    } else if (targetStars == '5★ 20/20') {
      hpBonus = 60 * 2; restBonus = 60 * 1; // 3→4→5→5+
    }
  } else if (baseRarity == 4) {
    if (targetStars == '5★') {
      hpBonus = 20 * 2; restBonus = 20 * 1; // 4→5
    } else if (targetStars == '5★ 20/20') {
      hpBonus = 40 * 2; restBonus = 40 * 1; // 4→5→5+
    }
  } else {
    // 5★ base
    if (targetStars == '5★ 20/20') {
      hpBonus = 20 * 5; restBonus = 20 * 2; // 5→5+
    }
  }

  return {
    'hp': hpBonus, 'atk': restBonus, 'def': restBonus,
    'spa': restBonus, 'spd': restBonus, 'spe': restBonus,
  };
}

/// Returns the list of available star levels for a pair.
List<String> availableStarLevels(int baseRarity, bool hasEx) {
  final levels = <String>[];
  for (int s = baseRarity; s <= 4; s++) {
    levels.add('$s★');
  }
  levels.add('5★');
  levels.add('5★ 20/20');
  return levels;
}

/// Default star level for a pair.
String defaultStarLevel(bool hasEx) => '5★ 20/20';

const exBaseBonus = {
  'hp': 100, 'atk': 40, 'def': 40, 'spa': 40, 'spd': 40, 'spe': 40,
};

const exRoleBonusMap = <String, Map<String, int>>{
  'Strike': {'hp': 60, 'atk': 40, 'spa': 40},
  'Tech': {'hp': 60, 'def': 20, 'spa': 20, 'spd': 20},
  'Support': {'hp': 60, 'def': 40, 'spd': 40},
  'Sprint': {'hp': 60, 'atk': 20, 'spa': 40, 'spe': 40},
  'Field': {'hp': 60, 'def': 20, 'spd': 20, 'spe': 40},
};
