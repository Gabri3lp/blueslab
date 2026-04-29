import 'future_rules.dart';

class ParsedData {
  const ParsedData({required this.pairs});

  final List<SyncPairData> pairs;
}

class SyncPairData {
  const SyncPairData({
    required this.number,
    required this.displayName,
    required this.role,
    this.exRole = '',
    required this.type,
    this.rarity = 5,
    this.hasEx = false,
    this.hasSuperAwakening = false,
    required this.cells,
    this.releaseDate,
    this.syncMoveName = '',
    this.weakness = '',
    this.moves = const [],
    this.passives = const [],
    this.description = '',
    this.hasTera = false,
    this.teraMove,
    this.teraPassives = const [],
    this.stats = const {},
    this.teraStatMultiplier = const {},
    this.megaStatMultiplier = const {},
    this.megaStats = const {},
    this.formStats = const {},
    this.variations = const [],
    this.tags = const [],
    this.rules = const [],
  });

  final int number;
  final String displayName;
  final String role;
  final String exRole;
  final String type;
  final String weakness;
  final int rarity;
  final bool hasEx;
  final bool hasSuperAwakening;
  final List<GridCellData> cells;
  final DateTime? releaseDate;
  final String syncMoveName;
  final List<MoveData> moves;
  final List<PassiveData> passives;
  final String description;
  final bool hasTera;
  final MoveData? teraMove;
  final List<PassiveData> teraPassives;
  final Map<String, Map<String, int>> stats;
  final Map<String, double> teraStatMultiplier;
  final Map<String, double> megaStatMultiplier;
  final Map<String, Map<String, int>> megaStats;
  final Map<String, Map<String, Map<String, int>>> formStats;
  final List<VariationData> variations;
  final List<PairTag> tags;
  final List<PassiveRule> rules;

  Iterable<String> get searchTerms sync* {
    yield displayName;
    yield role;
    yield exRole;
    yield type;
    yield weakness;
    for (final move in moves) {
      yield* move.searchTerms;
    }
    for (final passive in passives) {
      yield passive.name;
      yield passive.description;
    }
    for (final tag in tags) {
      yield tag.category;
      yield tag.value;
    }
  }
}

class GridCellData {
  const GridCellData({
    required this.cellNumber,
    required this.q,
    required this.r,
    required this.s,
    required this.energyCost,
    required this.orbCost,
    required this.title,
    required this.description,
    required this.colorKind,
    this.moveLevel = 1,
    this.tags = const [],
    this.effects = const [],
  });

  final int cellNumber;
  final int q;
  final int r;
  final int s;
  final int energyCost;
  final int orbCost;
  final String title;
  final String description;
  final String colorKind;
  final int moveLevel;
  final List<PairTag> tags;
  final List<PassiveEffect> effects;
}

class MoveData {
  const MoveData({
    required this.name,
    this.type = '',
    this.category = '',
    this.power = '',
    this.accuracy = '',
    this.gauge = '',
    this.target = '',
    this.description = '',
    this.isSync = false,
    this.slot,
    this.tags = const [],
    this.effects = const [],
  });

  final String name;
  final String type;
  final String category;
  final String power;
  final String accuracy;
  final String gauge;
  final String target;
  final String description;
  final bool isSync;
  final int? slot;
  final List<PairTag> tags;
  final List<PassiveEffect> effects;

  Iterable<String> get searchTerms sync* {
    yield name;
    yield type;
    yield category;
    yield target;
    yield description;
    for (final tag in tags) {
      yield tag.category;
      yield tag.value;
    }
  }
}

class PassiveData {
  const PassiveData({
    required this.name,
    required this.description,
    this.tags = const [],
    this.rule = const PassiveRule(),
    this.locked = false,
  });

  final String name;
  final String description;
  final List<PairTag> tags;
  final PassiveRule rule;
  final bool locked;
}

class VariationData {
  const VariationData({
    required this.formName,
    this.moves = const [],
    this.passives = const [],
  });

  final String formName;
  final List<MoveData> moves;
  final List<PassiveData> passives;

  List<MoveData> applyTo(List<MoveData> baseMoves) {
    final result = List<MoveData>.from(baseMoves);
    for (final vm in moves) {
      if (vm.isSync) {
        final idx = result.indexWhere((move) => move.isSync);
        if (idx >= 0) {
          result[idx] = vm;
        } else {
          result.add(vm);
        }
        continue;
      }

      if (vm.slot == null) {
        result.add(vm);
        continue;
      }

      final slotIndex = vm.slot! - 1;
      final nonSyncMoves = result.where((move) => !move.isSync).toList();
      if (slotIndex < 0 || slotIndex >= nonSyncMoves.length) {
        result.add(vm);
        continue;
      }

      var seenMoves = 0;
      for (var index = 0; index < result.length; index++) {
        if (result[index].isSync) {
          continue;
        }
        if (seenMoves == slotIndex) {
          result[index] = vm;
          break;
        }
        seenMoves++;
      }
    }
    return result;
  }
}
