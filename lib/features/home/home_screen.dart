import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../damage/calc.dart';
import '../../data/sync_pair_repository.dart';
import '../../models/sync_pair_models.dart';
import '../../star_level.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  static const _repository = SyncPairRepository();

  late final Future<ParsedData> _dataFuture = _repository.load();
  int _selectedPairIndex = 0;
  final Set<int> _activeCells = <int>{};
  bool _hardCap = true;
  int _moveLevel = 5;
  int _rightTab = 1;
  bool _initialActivationDone = false;
  bool _expandedRight = false;

  static const _hexDirections = [
    [1, 0, -1],
    [-1, 0, 1],
    [0, 1, -1],
    [0, -1, 1],
    [1, -1, 0],
    [-1, 1, 0],
  ];

  bool _isAdjacentToCenter(GridCellData cell) {
    for (final d in _hexDirections) {
      if (cell.q == d[0] && cell.r == d[1] && cell.s == d[2]) return true;
    }
    return false;
  }

  bool _isAdjacentToActiveOrCenter(
    GridCellData cell,
    List<GridCellData> allCells,
  ) {
    for (final d in _hexDirections) {
      final nq = cell.q + d[0];
      final nr = cell.r + d[1];
      final ns = cell.s + d[2];
      if (nq == 0 && nr == 0 && ns == 0) return true;
      for (final other in allCells) {
        if (other.q == nq &&
            other.r == nr &&
            other.s == ns &&
            _activeCells.contains(other.cellNumber)) {
          return true;
        }
      }
    }
    return false;
  }

  void _pruneDisconnected(List<GridCellData> allCells) {
    final cellMap = <String, GridCellData>{};
    for (final c in allCells) {
      cellMap['${c.q},${c.r},${c.s}'] = c;
    }
    // BFS from center (0,0,0) through active cells.
    final connected = <int>{};
    final queue = <List<int>>[
      [0, 0, 0],
    ];
    final visited = <String>{'0,0,0'};
    while (queue.isNotEmpty) {
      final pos = queue.removeAt(0);
      for (final d in _hexDirections) {
        final nq = pos[0] + d[0];
        final nr = pos[1] + d[1];
        final ns = pos[2] + d[2];
        final key = '$nq,$nr,$ns';
        if (visited.contains(key)) continue;
        visited.add(key);
        final neighbor = cellMap[key];
        if (neighbor != null && _activeCells.contains(neighbor.cellNumber)) {
          connected.add(neighbor.cellNumber);
          queue.add([nq, nr, ns]);
        }
      }
    }
    _activeCells.retainAll(connected);
  }

  void _activateFreeCenterCells(List<GridCellData> cells) {
    for (final cell in cells) {
      if (cell.energyCost == 0 &&
          cell.moveLevel <= _moveLevel &&
          _isAdjacentToCenter(cell)) {
        _activeCells.add(cell.cellNumber);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: FutureBuilder<ParsedData>(
        future: _dataFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }

          if (snapshot.hasError) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Text('Error cargando datos: ${snapshot.error}'),
              ),
            );
          }

          final data = snapshot.data!;
          if (data.pairs.isEmpty) {
            return const Center(child: Text('No se encontraron personajes.'));
          }

          final selectedPair = data.pairs[_selectedPairIndex];

          if (_hardCap && !_initialActivationDone) {
            _initialActivationDone = true;
            _activateFreeCenterCells(selectedPair.cells);
          }

          final selectedEnergy =
              60 -
              selectedPair.cells
                  .where((c) => _activeCells.contains(c.cellNumber))
                  .fold<int>(0, (sum, c) => sum + c.energyCost);
          final selectedOrbs = selectedPair.cells
              .where((c) => _activeCells.contains(c.cellNumber))
              .fold<int>(0, (sum, c) => sum + c.orbCost);

          return Row(
            children: [
              Expanded(
                flex: _expandedRight ? 2 : 5,
                child: Column(
                  children: [
                    Padding(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 6,
                      ),
                      child: SingleChildScrollView(
                        scrollDirection: Axis.horizontal,
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Text('⚡ $selectedEnergy'),
                            const SizedBox(width: 12),
                            Text('🔮 $selectedOrbs'),
                            const SizedBox(width: 16),
                            for (int i = 1; i <= 5; i++)
                              Padding(
                                padding: const EdgeInsets.only(right: 2),
                                child: GestureDetector(
                                  onTap: () {
                                    setState(() {
                                      _moveLevel = i;
                                      _activeCells.removeWhere((cn) {
                                        final cell = selectedPair.cells
                                            .firstWhere(
                                              (c) => c.cellNumber == cn,
                                            );
                                        return cell.moveLevel > i;
                                      });
                                      if (_hardCap) {
                                        _pruneDisconnected(selectedPair.cells);
                                      }
                                    });
                                  },
                                  child: Image.asset(
                                    _moveLevel >= i
                                        ? 'assets/img/sync_level_on.png'
                                        : 'assets/img/sync_level_off.png',
                                    width: 32,
                                    height: 32,
                                  ),
                                ),
                              ),
                            const SizedBox(width: 8),
                            IconButton(
                              onPressed: _activeCells.isNotEmpty
                                  ? () => setState(() {
                                      _activeCells.clear();
                                      if (_hardCap) {
                                        _activateFreeCenterCells(
                                          selectedPair.cells,
                                        );
                                      }
                                    })
                                  : null,
                              icon: const Icon(Icons.restart_alt),
                              tooltip: 'Reset Grid',
                            ),
                            if (!_expandedRight) ...[
                              const SizedBox(width: 8),
                              const Text('Hard Cap'),
                              Switch(
                                value: _hardCap,
                                onChanged: (value) {
                                  setState(() {
                                    _hardCap = value;
                                    if (value) {
                                      _activateFreeCenterCells(
                                        selectedPair.cells,
                                      );
                                      _pruneDisconnected(selectedPair.cells);
                                    }
                                  });
                                },
                              ),
                            ],
                          ],
                        ),
                      ),
                    ),
                    Expanded(
                      child: Card(
                        margin: const EdgeInsets.fromLTRB(8, 8, 0, 8),
                        clipBehavior: Clip.antiAlias,
                        child: HexGridView(
                          cells: selectedPair.cells,
                          pairs: data.pairs,
                          activeCells: _activeCells,
                          syncMoveName: selectedPair.syncMoveName,
                          onToggleCell: (cellNumber) {
                            setState(() {
                              if (_activeCells.contains(cellNumber)) {
                                _activeCells.remove(cellNumber);
                                if (_hardCap) {
                                  _pruneDisconnected(selectedPair.cells);
                                }
                              } else {
                                final cell = selectedPair.cells.firstWhere(
                                  (c) => c.cellNumber == cellNumber,
                                );
                                if (cell.moveLevel > _moveLevel) return;
                                if (_hardCap &&
                                    !_isAdjacentToActiveOrCenter(
                                      cell,
                                      selectedPair.cells,
                                    )) {
                                  return;
                                }
                                _activeCells.add(cellNumber);
                              }
                            });
                          },
                          onSelectPair: (index) {
                            setState(() {
                              _selectedPairIndex = index;
                              _activeCells.clear();
                              if (_hardCap) {
                                _activateFreeCenterCells(
                                  data.pairs[index].cells,
                                );
                              }
                            });
                          },
                          moveLevel: _moveLevel,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const VerticalDivider(width: 1),
              Expanded(
                flex: _expandedRight ? 6 : 3,
                child: RightPanel(
                  pair: selectedPair,
                  activeCells: _activeCells,
                  selectedTab: _rightTab,
                  onTabChanged: (tab) => setState(() => _rightTab = tab),
                  moveLevel: _moveLevel,
                  expanded: _expandedRight,
                  onToggleExpand: () =>
                      setState(() => _expandedRight = !_expandedRight),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

class RightPanel extends StatelessWidget {
  const RightPanel({
    super.key,
    required this.pair,
    required this.activeCells,
    required this.selectedTab,
    required this.onTabChanged,
    required this.moveLevel,
    required this.expanded,
    required this.onToggleExpand,
  });

  final SyncPairData pair;
  final Set<int> activeCells;
  final int selectedTab;
  final ValueChanged<int> onTabChanged;
  final int moveLevel;
  final bool expanded;
  final VoidCallback onToggleExpand;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              IconButton(
                onPressed: onToggleExpand,
                icon: Icon(
                  expanded ? Icons.chevron_right : Icons.chevron_left,
                  size: 20,
                ),
                tooltip: expanded ? 'Collapse' : 'Expand',
                visualDensity: VisualDensity.compact,
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      pair.displayName,
                      style: Theme.of(context).textTheme.titleLarge,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    if (pair.releaseDate != null)
                      Text(
                        'Available: ${pair.releaseDate!.day}/${pair.releaseDate!.month}/${pair.releaseDate!.year}',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: FilledButton(
                  onPressed: selectedTab == 0 ? null : () => onTabChanged(0),
                  child: const Text('Overview'),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: FilledButton(
                  onPressed: selectedTab == 1 ? null : () => onTabChanged(1),
                  child: const Text('Calculadora'),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          const Divider(height: 1),
          const SizedBox(height: 8),
          Expanded(
            child: selectedTab == 0
                ? SyncPairOverview(
                    pair: pair,
                    moveLevel: moveLevel,
                    activeCells: activeCells,
                  )
                : DamageCalculatorPanel(
                    key: ValueKey(pair.number),
                    pair: pair,
                    activeCells: activeCells,
                    moveLevel: moveLevel,
                    expanded: expanded,
                  ),
          ),
        ],
      ),
    );
  }
}

const _typeColors = <String, Color>{
  'normal': Color(0xFFA8A878),
  'fire': Color(0xFFF08030),
  'water': Color(0xFF6890F0),
  'grass': Color(0xFF78C850),
  'electric': Color(0xFFF8D030),
  'ice': Color(0xFF98D8D8),
  'fighting': Color(0xFFC03028),
  'poison': Color(0xFFA040A0),
  'ground': Color(0xFFE0C068),
  'flying': Color(0xFFA890F0),
  'psychic': Color(0xFFF85888),
  'bug': Color(0xFFA8B820),
  'rock': Color(0xFFB8A038),
  'ghost': Color(0xFF705898),
  'dragon': Color(0xFF7038F8),
  'dark': Color(0xFF705848),
  'steel': Color(0xFFB8B8D0),
  'fairy': Color(0xFFEE99AC),
  'stellar': Color(0xFF40B5A5),
};

const _typeIcons = <String, String>{
  'normal': 'assets/pomatools.github.io-master/assets/img/battle/TYPE_001.png',
  'fire': 'assets/pomatools.github.io-master/assets/img/battle/TYPE_002.png',
  'water': 'assets/pomatools.github.io-master/assets/img/battle/TYPE_003.png',
  'electric':
      'assets/pomatools.github.io-master/assets/img/battle/TYPE_004.png',
  'grass': 'assets/pomatools.github.io-master/assets/img/battle/TYPE_005.png',
  'ice': 'assets/pomatools.github.io-master/assets/img/battle/TYPE_006.png',
  'fighting':
      'assets/pomatools.github.io-master/assets/img/battle/TYPE_007.png',
  'poison': 'assets/pomatools.github.io-master/assets/img/battle/TYPE_008.png',
  'ground': 'assets/pomatools.github.io-master/assets/img/battle/TYPE_009.png',
  'flying': 'assets/pomatools.github.io-master/assets/img/battle/TYPE_010.png',
  'psychic': 'assets/pomatools.github.io-master/assets/img/battle/TYPE_011.png',
  'bug': 'assets/pomatools.github.io-master/assets/img/battle/TYPE_012.png',
  'rock': 'assets/pomatools.github.io-master/assets/img/battle/TYPE_013.png',
  'ghost': 'assets/pomatools.github.io-master/assets/img/battle/TYPE_014.png',
  'dragon': 'assets/pomatools.github.io-master/assets/img/battle/TYPE_015.png',
  'dark': 'assets/pomatools.github.io-master/assets/img/battle/TYPE_016.png',
  'steel': 'assets/pomatools.github.io-master/assets/img/battle/TYPE_017.png',
  'fairy': 'assets/pomatools.github.io-master/assets/img/battle/TYPE_018.png',
  'stellar': 'assets/pomatools.github.io-master/assets/img/battle/TYPE_099.png',
};

enum _MasterPassiveCategory { any, physical, special }

class _MasterPassiveEffect {
  const _MasterPassiveEffect({
    required this.name,
    required this.description,
    required this.theme,
    required this.basePowerUp,
    required this.perAdditionalAlly,
    required this.maxPowerUp,
    required this.appliesToSync,
    required this.category,
  });

  final String name;
  final String description;
  final String theme;
  final double basePowerUp;
  final double perAdditionalAlly;
  final double maxPowerUp;
  final bool appliesToSync;
  final _MasterPassiveCategory category;

  double powerUpForAdditionalAllies(int additionalAllies) {
    final extra = additionalAllies.clamp(0, 2);
    final powerUp = basePowerUp + perAdditionalAlly * extra;
    return powerUp > maxPowerUp ? maxPowerUp : powerUp;
  }

  bool appliesToMove(MoveData move) {
    final isPhysical = move.category.toLowerCase() == 'physical';
    final isSpecial = move.category.toLowerCase() == 'special';
    if (move.isSync && !appliesToSync) return false;
    return switch (category) {
      _MasterPassiveCategory.any => true,
      _MasterPassiveCategory.physical => isPhysical,
      _MasterPassiveCategory.special => isSpecial,
    };
  }
}

class SyncPairOverview extends StatefulWidget {
  const SyncPairOverview({
    super.key,
    required this.pair,
    required this.moveLevel,
    required this.activeCells,
  });

  final SyncPairData pair;
  final int moveLevel;
  final Set<int> activeCells;

  @override
  State<SyncPairOverview> createState() => _SyncPairOverviewState();
}

class _SyncPairOverviewState extends State<SyncPairOverview> {
  int _formIndex = 0;
  String _level = '200';
  String? _starLevel;
  bool _exRoleActive = true;

  @override
  void didUpdateWidget(covariant SyncPairOverview oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.pair.number != oldWidget.pair.number) {
      _starLevel = null;
    }
  }

  String get _effectiveStarLevel {
    final valid = availableStarLevels(pair.rarity, pair.hasEx);
    if (_starLevel != null && valid.contains(_starLevel)) return _starLevel!;
    return valid.last;
  } // 0=Base, 1..N=variations, last=Tera

  SyncPairData get pair => widget.pair;
  bool get _showTera =>
      pair.hasTera && _formIndex == pair.variations.length + 1;
  bool get _isVariation =>
      _formIndex > 0 && _formIndex <= pair.variations.length;
  VariationData? get _activeVariation =>
      _isVariation ? pair.variations[_formIndex - 1] : null;

  int _gridBonus2(String statKey) {
    const mapping = {
      'hp': 'HP',
      'atk': 'Attack',
      'def': 'Defense',
      'spa': 'Sp. Atk',
      'spd': 'Sp. Def',
      'spe': 'Speed',
    };
    final prefix = mapping[statKey] ?? '';
    if (prefix.isEmpty) return 0;
    int total = 0;
    for (final cell in pair.cells) {
      if (!widget.activeCells.contains(cell.cellNumber)) continue;
      final t = cell.title.trim();
      if (t.startsWith(prefix)) {
        final val = int.tryParse(t.substring(prefix.length).trim());
        if (val != null) total += val;
      }
    }
    return total;
  }

  Map<String, int> _potentialBonus() => calcPotentialBonus(
    baseRarity: pair.rarity,
    targetStars: _effectiveStarLevel,
  );

  bool get _exActive => _effectiveStarLevel == '5★ EX';

  bool get _megaActiveOverview {
    if (pair.megaStatMultiplier.isEmpty) return false;
    int megaIdx = pair.variations.length + 1;
    if (pair.hasTera) megaIdx++;
    return _formIndex == megaIdx;
  }

  int _exBonusOverview(String stat) {
    if (!_exActive || !pair.hasEx) return 0;
    int total = exBaseBonus[stat] ?? 0;
    if (_exRoleActive && pair.exRole.isNotEmpty) {
      total += exRoleBonusMap[pair.exRole]?[stat] ?? 0;
    }
    return total;
  }

  double _megaMultOverview(String stat) {
    if (!_megaActiveOverview) return 1.0;
    return pair.megaStatMultiplier[stat] ?? 1.0;
  }

  int _applyFormMultiplier(
    int value,
    double mult,
    String stat, {
    bool useExactMegaRatio = false,
  }) {
    if (mult == 1.0) return value;
    return (value * mult).ceil() - 1;
  }

  Map<String, int> _interpolatedStats() {
    if (pair.stats.isEmpty) return {};
    return pair.stats[_level] ?? pair.stats.values.last;
  }

  int _overviewTotal(String stat, int baseStat) {
    final pot = _potentialBonus()[stat] ?? 0;
    final beforeMega = baseStat + pot + _exBonusOverview(stat);
    final mult = _megaMultOverview(stat);
    return _applyFormMultiplier(
      beforeMega,
      mult,
      stat,
      useExactMegaRatio: _megaActiveOverview,
    );
  }

  Widget _formTab(String label, int index, {Color? color}) {
    final selected = _formIndex == index;
    final tabColor = color ?? Theme.of(context).colorScheme.primary;
    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() => _formIndex = index),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(
            color: selected ? tabColor : Colors.transparent,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: tabColor, width: 1.5),
          ),
          alignment: Alignment.center,
          child: Text(
            label,
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w700,
              color: selected
                  ? Colors.white
                  : Theme.of(context).colorScheme.onSurface,
            ),
          ),
        ),
      ),
    );
  }

  Color _typeColor(String type) {
    return _typeColors[type.toLowerCase()] ?? Colors.grey;
  }

  bool get _isEx => _effectiveStarLevel == '5★ EX';

  bool get _syncTechExBoost {
    if (!_isEx || !pair.hasEx) return false;
    final role = pair.role.toLowerCase().trim();
    final exRole = pair.exRole.toLowerCase().trim();
    return role == 'tech' || (_exRoleActive && exRole == 'tech');
  }

  String _scaledPower(String rawPower, [int? moveLevel]) {
    final match = RegExp(r'^(\d+)').firstMatch(rawPower);
    if (match == null) return rawPower;
    final base = int.parse(match.group(1)!);
    final level = moveLevel ?? widget.moveLevel;
    return '${(base * (1 + 0.05 * (level - 1))).floor()}';
  }

  int _gridBonus(String moveName, String stat) {
    int total = 0;
    final prefix = '$moveName: $stat ';
    for (final cell in widget.pair.cells) {
      if (!widget.activeCells.contains(cell.cellNumber)) continue;
      if (!cell.title.startsWith(prefix)) continue;
      final numStr = cell.title.substring(prefix.length).trim();
      final val = int.tryParse(numStr);
      if (val != null) total += val;
    }
    return total;
  }

  Widget _typeChip(String type) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: _typeColor(type),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(
        type,
        style: const TextStyle(
          color: Colors.white,
          fontSize: 12,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }

  Widget _moveCard(BuildContext context, MoveData move, String teraMoveName) {
    return _MoveCard(
      move: move,
      typeColor: _typeColor(move.type),
      typeChip: move.type.isNotEmpty ? _typeChip(move.type) : null,
      powerBonus: _gridBonus(move.name, 'Power'),
      accBonus: _gridBonus(move.name, 'Accuracy'),
      basePower: _scaledPower(move.power, widget.moveLevel),
      teraBoost:
          _showTera &&
          move.type.toLowerCase() == pair.type.toLowerCase() &&
          move.name != teraMoveName &&
          !move.isSync,
      syncTechBoost: move.isSync && _syncTechExBoost,
    );
  }

  Widget _passiveCard(BuildContext context, PassiveData passive) {
    return _PassiveCard(passive: passive);
  }

  @override
  Widget build(BuildContext context) {
    // Build display moves based on active form
    List<MoveData> displayMoves;
    List<PassiveData> displayPassives;
    if (_showTera) {
      displayMoves = [...pair.moves, if (pair.teraMove != null) pair.teraMove!];
      displayPassives = [
        for (int i = 0; i < pair.passives.length; i++)
          i < pair.teraPassives.length
              ? pair.teraPassives[i]
              : pair.passives[i],
      ];
    } else if (_isVariation && _activeVariation != null) {
      displayMoves = _activeVariation!.applyTo(pair.moves);
      displayPassives = [
        for (int i = 0; i < pair.passives.length; i++)
          i < _activeVariation!.passives.length
              ? _activeVariation!.passives[i]
              : pair.passives[i],
      ];
    } else {
      displayMoves = pair.moves;
      displayPassives = pair.passives;
    }
    final teraMoveName = pair.teraMove?.name ?? '';

    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              if (pair.role.isNotEmpty)
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 2,
                  ),
                  decoration: BoxDecoration(
                    color: Colors.blueGrey,
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    pair.role,
                    style: const TextStyle(color: Colors.white, fontSize: 12),
                  ),
                ),
              if (pair.exRole.isNotEmpty) ...[
                const SizedBox(width: 4),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 2,
                  ),
                  decoration: BoxDecoration(
                    color: Colors.deepPurple,
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    'EX: ${pair.exRole}',
                    style: const TextStyle(color: Colors.white, fontSize: 12),
                  ),
                ),
              ],
              const SizedBox(width: 6),
              if (pair.type.isNotEmpty) _typeChip(pair.type),
            ],
          ),
          if (pair.hasTera ||
              pair.variations.isNotEmpty ||
              pair.megaStatMultiplier.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(top: 10),
              child: Row(
                children: [
                  _formTab('Base', 0),
                  for (int i = 0; i < pair.variations.length; i++) ...[
                    const SizedBox(width: 6),
                    _formTab(
                      pair.variations[i].formName,
                      i + 1,
                      color: Colors.teal,
                    ),
                  ],
                  if (pair.hasTera) ...[
                    const SizedBox(width: 6),
                    _formTab(
                      'Tera',
                      pair.variations.length + 1,
                      color: const Color(0xFF6C5CE7),
                    ),
                  ],
                  if (pair.megaStatMultiplier.isNotEmpty) ...[
                    const SizedBox(width: 6),
                    Builder(
                      builder: (_) {
                        int megaIdx = pair.variations.length + 1;
                        if (pair.hasTera) megaIdx++;
                        return _formTab(
                          'Mega',
                          megaIdx,
                          color: Colors.deepOrange,
                        );
                      },
                    ),
                  ],
                ],
              ),
            ),
          if (pair.stats.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(top: 12, bottom: 4),
              child: Builder(
                builder: (_) {
                  final s = _interpolatedStats();
                  const labels = [
                    'HP',
                    'Atk',
                    'Def',
                    'Sp.Atk',
                    'Sp.Def',
                    'Spe',
                  ];
                  const keys = ['hp', 'atk', 'def', 'spa', 'spd', 'spe'];
                  final levels = pair.stats.keys.toList()
                    ..sort((a, b) => int.parse(a).compareTo(int.parse(b)));
                  if (!levels.contains(_level)) _level = levels.last;
                  return Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Theme.of(
                        context,
                      ).colorScheme.primary.withValues(alpha: 0.06),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            const Text(
                              'Stats',
                              style: TextStyle(
                                fontWeight: FontWeight.w700,
                                fontSize: 12,
                              ),
                            ),
                            const SizedBox(width: 8),
                            DropdownButton<String>(
                              value: _level,
                              isDense: true,
                              underline: const SizedBox(),
                              style: const TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.w600,
                                color: Colors.black,
                              ),
                              items: [
                                for (final lv in levels)
                                  DropdownMenuItem(
                                    value: lv,
                                    child: Text('Lv. $lv'),
                                  ),
                              ],
                              onChanged: (v) => setState(() => _level = v!),
                            ),
                            const Spacer(),
                            DropdownButton<String>(
                              value: _effectiveStarLevel,
                              isDense: true,
                              underline: const SizedBox(),
                              style: const TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.w600,
                                color: Colors.black,
                              ),
                              items: [
                                for (final sl in availableStarLevels(
                                  pair.rarity,
                                  pair.hasEx,
                                ))
                                  DropdownMenuItem(value: sl, child: Text(sl)),
                              ],
                              onChanged: (v) => setState(() => _starLevel = v!),
                            ),
                            if (pair.hasEx && pair.exRole.isNotEmpty) ...[
                              const SizedBox(width: 4),
                              FilterChip(
                                label: Text(
                                  'EX ${pair.exRole}',
                                  style: const TextStyle(fontSize: 10),
                                ),
                                selected: _exRoleActive,
                                showCheckmark: false,
                                onSelected: (v) => setState(() {
                                  _exRoleActive = v;
                                }),
                                selectedColor: Colors.indigo,
                                visualDensity: VisualDensity.compact,
                              ),
                            ],
                          ],
                        ),
                        const SizedBox(height: 6),
                        Row(
                          children: [
                            const SizedBox(width: 30),
                            for (int i = 0; i < 6; i++)
                              Expanded(
                                child: Center(
                                  child: Text(
                                    labels[i],
                                    style: const TextStyle(
                                      fontSize: 10,
                                      fontWeight: FontWeight.w700,
                                    ),
                                  ),
                                ),
                              ),
                          ],
                        ),
                        const SizedBox(height: 2),
                        Row(
                          children: [
                            const SizedBox(
                              width: 30,
                              child: Text(
                                'Base',
                                style: TextStyle(
                                  fontSize: 9,
                                  color: Colors.grey,
                                ),
                              ),
                            ),
                            for (int i = 0; i < 6; i++)
                              Expanded(
                                child: Center(
                                  child: Text(
                                    '${_overviewTotal(keys[i], s[keys[i]] ?? 0)}',
                                    style: const TextStyle(fontSize: 11),
                                  ),
                                ),
                              ),
                          ],
                        ),
                        Row(
                          children: [
                            const SizedBox(
                              width: 30,
                              child: Text(
                                'Grid',
                                style: TextStyle(
                                  fontSize: 9,
                                  color: Colors.grey,
                                ),
                              ),
                            ),
                            for (int i = 0; i < 6; i++)
                              Expanded(
                                child: Center(
                                  child: Builder(
                                    builder: (_) {
                                      final g = _gridBonus2(keys[i]);
                                      return Text(
                                        g > 0 ? '+$g' : '-',
                                        style: TextStyle(
                                          fontSize: 11,
                                          color: g > 0
                                              ? Theme.of(
                                                  context,
                                                ).colorScheme.primary
                                              : Colors.grey,
                                        ),
                                      );
                                    },
                                  ),
                                ),
                              ),
                          ],
                        ),
                        Builder(
                          builder: (_) {
                            return Row(
                              children: [
                                const SizedBox(
                                  width: 30,
                                  child: Text(
                                    'Total',
                                    style: TextStyle(
                                      fontSize: 9,
                                      fontWeight: FontWeight.w700,
                                    ),
                                  ),
                                ),
                                for (int i = 0; i < 6; i++)
                                  Expanded(
                                    child: Center(
                                      child: Builder(
                                        builder: (_) {
                                          final base = s[keys[i]] ?? 0;
                                          final grid = _gridBonus2(keys[i]);
                                          return Text(
                                            '${_overviewTotal(keys[i], base) + grid}',
                                            style: const TextStyle(
                                              fontSize: 12,
                                              fontWeight: FontWeight.w700,
                                            ),
                                          );
                                        },
                                      ),
                                    ),
                                  ),
                              ],
                            );
                          },
                        ),
                      ],
                    ),
                  );
                },
              ),
            ),
          if (pair.passives.isNotEmpty) ...[
            const Padding(
              padding: EdgeInsets.only(top: 16, bottom: 8),
              child: Text(
                'Passives',
                style: TextStyle(fontWeight: FontWeight.w700, fontSize: 14),
              ),
            ),
            for (final passive in displayPassives)
              _passiveCard(context, passive),
          ],
          if (pair.moves.isNotEmpty) ...[
            const Padding(
              padding: EdgeInsets.only(top: 8, bottom: 8),
              child: Text(
                'Moves',
                style: TextStyle(fontWeight: FontWeight.w700, fontSize: 14),
              ),
            ),
            for (final move in displayMoves)
              _moveCard(context, move, teraMoveName),
          ],
        ],
      ),
    );
  }
}

class _MoveCard extends StatefulWidget {
  const _MoveCard({
    required this.move,
    required this.typeColor,
    this.typeChip,
    required this.powerBonus,
    required this.accBonus,
    required this.basePower,
    this.teraBoost = false,
    this.syncTechBoost = false,
  });
  final MoveData move;
  final Color typeColor;
  final Widget? typeChip;
  final int powerBonus;
  final int accBonus;
  final String basePower;
  final bool teraBoost;
  final bool syncTechBoost;
  @override
  State<_MoveCard> createState() => _MoveCardState();
}

class _MoveCardState extends State<_MoveCard> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    final move = widget.move;
    final hasDesc = move.description.isNotEmpty;
    final basePowerNum = int.tryParse(widget.basePower);
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: move.type.isNotEmpty
            ? widget.typeColor.withValues(alpha: 0.12)
            : Theme.of(context).colorScheme.surface,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: move.type.isNotEmpty
              ? widget.typeColor.withValues(alpha: 0.5)
              : Colors.grey.shade300,
        ),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(8),
        onTap: hasDesc ? () => setState(() => _expanded = !_expanded) : null,
        child: Padding(
          padding: const EdgeInsets.all(10),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  if (move.isSync)
                    Padding(
                      padding: const EdgeInsets.only(right: 6),
                      child: Icon(
                        Icons.star,
                        size: 14,
                        color: Colors.purple.shade300,
                      ),
                    ),
                  Expanded(
                    child: Text(
                      move.name,
                      style: const TextStyle(
                        fontWeight: FontWeight.w700,
                        fontSize: 13,
                      ),
                    ),
                  ),
                  if (hasDesc)
                    Padding(
                      padding: const EdgeInsets.only(right: 4),
                      child: Icon(
                        _expanded ? Icons.expand_less : Icons.expand_more,
                        size: 18,
                        color: Theme.of(
                          context,
                        ).colorScheme.onSurface.withValues(alpha: 0.5),
                      ),
                    ),
                  if (widget.typeChip != null) widget.typeChip!,
                ],
              ),
              if (_expanded && hasDesc)
                Padding(
                  padding: const EdgeInsets.only(top: 4),
                  child: Text(
                    move.description,
                    style: TextStyle(
                      fontSize: 11,
                      color: Theme.of(
                        context,
                      ).colorScheme.onSurface.withValues(alpha: 0.7),
                    ),
                  ),
                ),
              if (move.power.isNotEmpty ||
                  move.accuracy.isNotEmpty ||
                  move.gauge.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(top: 6),
                  child: Wrap(
                    spacing: 12,
                    children: [
                      if (move.power.isNotEmpty && move.power != '--')
                        Builder(
                          builder: (_) {
                            final base = basePowerNum ?? 0;
                            final syncTechBase = widget.syncTechBoost
                                ? (base * 1.5).floor()
                                : base;
                            final teraBase = widget.teraBoost
                                ? (syncTechBase * 1.5).floor()
                                : syncTechBase;
                            final finalPower = teraBase + widget.powerBonus;
                            String label;
                            if (widget.teraBoost &&
                                widget.powerBonus > 0 &&
                                basePowerNum != null) {
                              label =
                                  '⚔ ${widget.basePower} × 1.5 = $teraBase + ${widget.powerBonus} = $finalPower';
                            } else if (widget.teraBoost &&
                                basePowerNum != null) {
                              label = '⚔ ${widget.basePower} × 1.5 = $teraBase';
                            } else if (widget.syncTechBoost &&
                                widget.powerBonus > 0 &&
                                basePowerNum != null) {
                              label =
                                  '⚔ ${widget.basePower} × 1.5 = $syncTechBase + ${widget.powerBonus} = $finalPower';
                            } else if (widget.syncTechBoost &&
                                basePowerNum != null) {
                              label =
                                  '⚔ ${widget.basePower} × 1.5 = $syncTechBase';
                            } else if (widget.powerBonus > 0 &&
                                basePowerNum != null) {
                              label =
                                  '⚔ ${widget.basePower} + ${widget.powerBonus} = $finalPower';
                            } else {
                              label = '⚔ ${widget.basePower}';
                            }
                            return Text(
                              label,
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight:
                                    (widget.powerBonus > 0 || widget.teraBoost)
                                    ? FontWeight.w700
                                    : FontWeight.normal,
                              ),
                            );
                          },
                        ),
                      if (move.accuracy.isNotEmpty && move.accuracy != '--')
                        Builder(
                          builder: (_) {
                            final baseAcc = int.tryParse(move.accuracy);
                            return Text(
                              widget.accBonus > 0 && baseAcc != null
                                  ? '🎯 ${move.accuracy} + ${widget.accBonus} = ${baseAcc + widget.accBonus}'
                                  : '🎯 ${move.accuracy}',
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: widget.accBonus > 0
                                    ? FontWeight.w700
                                    : FontWeight.normal,
                              ),
                            );
                          },
                        ),
                      if (move.gauge.isNotEmpty && move.gauge != '--')
                        Text(
                          '⚡ ${move.gauge}',
                          style: const TextStyle(fontSize: 11),
                        ),
                      if (move.target.isNotEmpty && move.target != '--')
                        Text(
                          '🎯 ${move.target}',
                          style: const TextStyle(fontSize: 11),
                        ),
                      if (move.category.isNotEmpty)
                        Text(
                          move.category,
                          style: TextStyle(
                            fontSize: 11,
                            color: Theme.of(
                              context,
                            ).colorScheme.onSurface.withValues(alpha: 0.5),
                          ),
                        ),
                    ],
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class _PassiveCard extends StatefulWidget {
  const _PassiveCard({required this.passive});
  final PassiveData passive;
  @override
  State<_PassiveCard> createState() => _PassiveCardState();
}

class _PassiveCardState extends State<_PassiveCard> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: Colors.amber.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.amber.withValues(alpha: 0.3)),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(8),
        onTap: widget.passive.description.isNotEmpty
            ? () => setState(() => _expanded = !_expanded)
            : null,
        child: Padding(
          padding: const EdgeInsets.all(10),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Flexible(
                    child: Text(
                      widget.passive.name,
                      style: const TextStyle(
                        fontWeight: FontWeight.w700,
                        fontSize: 13,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
                  if (widget.passive.description.isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(left: 4),
                      child: Icon(
                        _expanded ? Icons.expand_less : Icons.expand_more,
                        size: 18,
                        color: Theme.of(
                          context,
                        ).colorScheme.onSurface.withValues(alpha: 0.5),
                      ),
                    ),
                ],
              ),
              if (_expanded && widget.passive.description.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(top: 6),
                  child: Text(
                    widget.passive.description,
                    style: TextStyle(
                      fontSize: 11,
                      color: Theme.of(
                        context,
                      ).colorScheme.onSurface.withValues(alpha: 0.7),
                    ),
                    textAlign: TextAlign.center,
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class DamageCalculatorPanel extends StatefulWidget {
  const DamageCalculatorPanel({
    super.key,
    required this.pair,
    required this.activeCells,
    required this.moveLevel,
    this.expanded = false,
  });

  final SyncPairData pair;
  final Set<int> activeCells;
  final int moveLevel;
  final bool expanded;

  @override
  State<DamageCalculatorPanel> createState() => _DamageCalculatorPanelState();
}

class _DamageCalculatorPanelState extends State<DamageCalculatorPanel> {
  String _selectedLevel = '200';
  String _starLevel = '5★ EX';
  bool _hasExRole = true;

  bool get _isEx => _starLevel == '5★ EX';

  String _scaledPower(String rawPower, [int? moveLevel]) {
    final match = RegExp(r'^(\d+)').firstMatch(rawPower);
    if (match == null) return rawPower;
    final base = int.parse(match.group(1)!);
    final level = moveLevel ?? widget.moveLevel;
    return '${(base * (1 + 0.05 * (level - 1))).floor()}';
  }

  int _calcFormIndex = 0; // 0=Base, 1..N=variations, then Tera, then Mega
  String _selectedZone = '';
  String _selectedTerrain = '';
  String _selectedWeather = '';
  bool _isZoneEx = false;
  bool _isTerrainEx = false;
  bool _isWeatherEx = false;
  bool _isCriticalMove = true;
  int _physicalBoostNext = 0;
  int _specialBoostNext = 0;
  bool _superEffectiveNext = false;
  bool _physicalBreak = false;
  bool _specialBreak = false;
  int _syncMoveBoostNext = 0;
  int _targetCount = 1;
  int _playerSyncBoosts = 0;
  int _enemySyncBoosts = 0;
  int _playerHpPercent = 100;
  int _enemyHpPercent = 100;

  bool get _isMegaSupport {
    final role = widget.pair.role.toLowerCase().trim();
    final exRole = widget.pair.exRole.toLowerCase().trim();
    return role == 'support' || exRole == 'support';
  }

  int get _megaSyncBaseBoosts {
    if (!_megaActive) return 0;
    return _isMegaSupport ? 2 : 1;
  }

  int get _effectivePlayerSyncBoosts {
    if (!_megaActive) return _playerSyncBoosts;
    return _playerSyncBoosts + _megaSyncBaseBoosts;
  }

  // Circles state: region -> {physical, special, defensive} -> {active, allyCount}
  static const _circleRegions = [
    'Kanto',
    'Johto',
    'Hoenn',
    'Sinnoh',
    'Unova',
    'Kalos',
    'Alola',
    'Galar',
    'Paldea',
    'Pasio',
  ];
  final Map<String, Map<String, bool>> _circleActive = {
    for (final r in _circleRegions)
      r: {'physical': false, 'special': false, 'defensive': false},
  };
  final Map<String, int> _circleAllyCount = {
    for (final r in _circleRegions) r: 0,
  };
  final Map<String, int> _masterPassiveAllyCount = {};

  List<_MasterPassiveEffect> get _masterPassives {
    final found = <_MasterPassiveEffect>[];
    for (final passive in widget.pair.passives) {
      final parsed = _parseMasterPassive(passive);
      if (parsed != null) {
        found.add(parsed);
        _masterPassiveAllyCount.putIfAbsent(parsed.name, () => 0);
      }
    }
    return found;
  }

  _MasterPassiveEffect? _parseMasterPassive(PassiveData passive) {
    final description = passive.description.trim();
    if (!description.contains('allied sync pairs')) return null;
    if (!description.contains('theme you have on your team') &&
        !description.contains('These percentages increase according')) {
      return null;
    }

    final themeMatch = RegExp(
      r'with the ([A-Za-z]+) theme you have on your team',
      caseSensitive: false,
    ).firstMatch(description);
    if (themeMatch == null) return null;
    final theme = themeMatch.group(1)!;

    final lower = description.toLowerCase();
    final category = lower.contains('physical attack moves')
        ? _MasterPassiveCategory.physical
        : lower.contains('special attack moves')
        ? _MasterPassiveCategory.special
        : _MasterPassiveCategory.any;
    final appliesToSync = lower.contains('sync move');

    final baseMatch = RegExp(
      r'Powers up .*? by (\d+)%',
      caseSensitive: false,
    ).firstMatch(description);
    final perAllyMatch = RegExp(
      r'Each additional sync pair powers up .*? by (\d+)%',
      caseSensitive: false,
    ).firstMatch(description);
    final maxMatch = RegExp(
      r'The maximum power-up is (\d+)%',
      caseSensitive: false,
    ).firstMatch(description);
    if (baseMatch == null || perAllyMatch == null || maxMatch == null) {
      return null;
    }

    return _MasterPassiveEffect(
      name: passive.name,
      description: description,
      theme: theme,
      basePowerUp: int.parse(baseMatch.group(1)!) / 100,
      perAdditionalAlly: int.parse(perAllyMatch.group(1)!) / 100,
      maxPowerUp: int.parse(maxMatch.group(1)!) / 100,
      appliesToSync: appliesToSync,
      category: category,
    );
  }

  double _masterPassivePowerUp(MoveData move) {
    double total = 0;
    for (final passive in _masterPassives) {
      if (!passive.appliesToMove(move)) continue;
      total += passive.powerUpForAdditionalAllies(
        _masterPassiveAllyCount[passive.name] ?? 0,
      );
    }
    return total;
  }

  List<CircleEffect> _activeCircles() {
    final list = <CircleEffect>[];
    for (final region in _circleRegions) {
      final allies = _circleAllyCount[region]!;
      for (final entry in _circleActive[region]!.entries) {
        if (entry.value) {
          final type = switch (entry.key) {
            'physical' => CircleType.physical,
            'special' => CircleType.special,
            _ => CircleType.defensive,
          };
          list.add(CircleEffect(type: type, allyCount: allies));
        }
      }
    }
    return list;
  }

  final _playerSyncBoostsController = TextEditingController(text: '0');
  final _enemySyncBoostsController = TextEditingController(text: '0');
  final _playerHpPercentController = TextEditingController(text: '100');
  final _enemyHpPercentController = TextEditingController(text: '100');

  String _zoneLabel(String zone) {
    if (zone.isEmpty) return 'None';
    return _isZoneEx ? 'EX $zone' : zone;
  }

  String _terrainLabel(String terrain) {
    if (terrain.isEmpty) return 'None';
    return _isTerrainEx ? 'EX $terrain' : terrain;
  }

  String _weatherLabel(String weather) {
    if (weather.isEmpty) return 'None';
    if (!_isWeatherEx) return weather;
    return (weather == 'Sunny' || weather == 'Rainy') ? 'EX $weather' : weather;
  }

  static const _statLabels = ['hp', 'atk', 'def', 'spa', 'spd', 'spe'];
  static const _playerStatNames = {
    'hp': 'HP',
    'atk': 'Atk',
    'def': 'Def',
    'spa': 'Sp.Atk',
    'spd': 'Sp.Def',
    'spe': 'Spe',
    'acc': 'Acc',
    'eva': 'Eva',
    'crit': 'Crit',
  };
  static const _enemyStatNames = {
    'hp': 'HP',
    'atk': 'Atk',
    'def': 'Def',
    'spa': 'Sp.Atk',
    'spd': 'Sp.Def',
    'spe': 'Spe',
  };
  final Map<String, int> _gear = {for (final s in _statLabels) s: 100};
  final Map<String, TextEditingController> _gearControllers = {
    for (final s in _statLabels) s: TextEditingController(text: '100'),
  };

  static const _enemyDefaults = {
    'hp': 1958000,
    'atk': 5400,
    'def': 95,
    'spa': 5400,
    'spd': 95,
    'spe': 72,
    'acc': 0,
    'eva': 0,
  };
  final Map<String, int> _enemy = {..._enemyDefaults};
  final Map<String, TextEditingController> _enemyControllers = {
    for (final e in _enemyDefaults.entries)
      e.key: TextEditingController(text: '${e.value}'),
  };

  String _enemyWeakness = '';
  final Map<String, int> _typeRebuffs = {
    for (final t in _allTypes.skip(1)) t: 0,
  };
  int _stellarRebuff = 0;
  final Map<String, int> _enemyMitigations = {
    'atk': 5,
    'def': 5,
    'spa': 5,
    'spd': 5,
    'spe': 5,
  };
  String _enemyStatusCondition = '';
  String _playerStatusCondition = '';
  final Map<String, bool> _enemyVolatile = {
    'confused': false,
    'flinching': false,
    'trapped': false,
    'restrained': false,
  };
  final Map<String, int> _playerStages = {
    'hp': 0,
    'atk': 6,
    'def': 6,
    'spa': 6,
    'spd': 6,
    'spe': 6,
    'acc': 6,
    'eva': 6,
    'crit': 3,
  };
  final Map<String, int> _enemyStages = {
    'hp': 0,
    'atk': -6,
    'def': -6,
    'spa': -6,
    'spd': -6,
    'spe': -6,
    'acc': -6,
    'eva': -6,
  };

  static const _allTypes = [
    '',
    'Normal',
    'Fire',
    'Water',
    'Grass',
    'Electric',
    'Ice',
    'Fighting',
    'Poison',
    'Ground',
    'Flying',
    'Psychic',
    'Bug',
    'Rock',
    'Ghost',
    'Dragon',
    'Dark',
    'Steel',
    'Fairy',
  ];
  static const _weaknessTypes = [
    '',
    'Fire',
    'Water',
    'Grass',
    'Electric',
    'Ice',
    'Fighting',
    'Poison',
    'Ground',
    'Flying',
    'Psychic',
    'Bug',
    'Rock',
    'Ghost',
    'Dragon',
    'Dark',
    'Steel',
    'Fairy',
  ];

  static const _zoneOptions = [
    '',
    'Normal Zone',
    'Ice Zone',
    'Fighting Zone',
    'Poison Zone',
    'Ground Zone',
    'Flying Zone',
    'Bug Zone',
    'Rock Zone',
    'Ghost Zone',
    'Dragon Zone',
    'Dark Zone',
    'Steel Zone',
    'Fairy Zone',
  ];
  static const _terrainOptions = [
    '',
    'Electric Terrain',
    'Psychic Terrain',
    'Grassy Terrain',
  ];
  static const _weatherOptions = ['', 'Sunny', 'Rainy', 'Hail', 'Sandstorm'];

  static const _zoneBoostType = {
    'Normal Zone': 'Normal',
    'Ice Zone': 'Ice',
    'Fighting Zone': 'Fighting',
    'Poison Zone': 'Poison',
    'Ground Zone': 'Ground',
    'Flying Zone': 'Flying',
    'Bug Zone': 'Bug',
    'Rock Zone': 'Rock',
    'Ghost Zone': 'Ghost',
    'Dragon Zone': 'Dragon',
    'Dark Zone': 'Dark',
    'Steel Zone': 'Steel',
    'Fairy Zone': 'Fairy',
  };
  static const _terrainBoostType = {
    'Electric Terrain': 'Electric',
    'Psychic Terrain': 'Psychic',
    'Grassy Terrain': 'Grass',
  };
  static const _weatherBoostType = {'Sunny': 'Fire', 'Rainy': 'Water'};

  static const Map<String, IconData> _fieldEffectIcons = {
    '': Icons.block,
    'Normal Zone': Icons.circle,
    'Ice Zone': Icons.ac_unit,
    'Fighting Zone': Icons.sports_mma,
    'Poison Zone': Icons.science,
    'Ground Zone': Icons.terrain,
    'Flying Zone': Icons.flight,
    'Bug Zone': Icons.bug_report,
    'Rock Zone': Icons.landscape,
    'Ghost Zone': Icons.visibility_off,
    'Dragon Zone': Icons.whatshot,
    'Dark Zone': Icons.dark_mode,
    'Steel Zone': Icons.construction,
    'Fairy Zone': Icons.auto_awesome,
    'Electric Terrain': Icons.flash_on,
    'Psychic Terrain': Icons.psychology,
    'Grassy Terrain': Icons.grass,
    'Sunny': Icons.wb_sunny,
    'Rainy': Icons.grain,
    'Hail': Icons.ac_unit,
    'Sandstorm': Icons.filter_drama,
  };

  @override
  void dispose() {
    for (final c in _gearControllers.values) {
      c.dispose();
    }
    for (final c in _enemyControllers.values) {
      c.dispose();
    }
    _playerSyncBoostsController.dispose();
    _enemySyncBoostsController.dispose();
    _playerHpPercentController.dispose();
    _enemyHpPercentController.dispose();
    super.dispose();
  }

  bool get _syncTechExBoost {
    if (!_isEx || !widget.pair.hasEx) return false;
    final role = widget.pair.role.toLowerCase().trim();
    final exRole = widget.pair.exRole.toLowerCase().trim();
    return role == 'tech' || (_hasExRole && exRole == 'tech');
  }

  int _potentialBonus(String stat) {
    return calcPotentialBonus(
          baseRarity: widget.pair.rarity,
          targetStars: _starLevel,
        )[stat] ??
        0;
  }

  int _exRoleBonus(String stat) {
    if (!_isEx ||
        !widget.pair.hasEx ||
        !_hasExRole ||
        widget.pair.exRole.isEmpty)
      return 0;
    return exRoleBonusMap[widget.pair.exRole]?[stat] ?? 0;
  }

  bool get _megaActive {
    final pair = widget.pair;
    if (pair.megaStatMultiplier.isEmpty && pair.megaStats.isEmpty) return false;
    int megaIdx = pair.variations.length + 1;
    if (pair.hasTera) megaIdx++;
    return _calcFormIndex == megaIdx;
  }

  bool get _hasMegaForm =>
      widget.pair.megaStatMultiplier.isNotEmpty ||
      widget.pair.megaStats.isNotEmpty;

  bool _usesMegaSyncStats(MoveData move) => move.isSync && _hasMegaForm;

  bool get _teraActive =>
      widget.pair.hasTera &&
      _calcFormIndex == widget.pair.variations.length + 1;

  double _teraStatMult(String stat) {
    if (!_teraActive) return 1.0;
    return widget.pair.teraStatMultiplier[stat] ?? 1.0;
  }

  double _megaStatMult(String stat, {bool forceMega = false}) {
    if (!_megaActive && !forceMega) return 1.0;
    return widget.pair.megaStatMultiplier[stat] ?? 1.0;
  }

  double _formStatMult(String stat, {bool forceMega = false}) {
    return _teraStatMult(stat) * _megaStatMult(stat, forceMega: forceMega);
  }

  int _applyFormMultiplier(
    int value,
    double mult,
    String stat, {
    bool useExactMegaRatio = false,
  }) {
    if (mult == 1.0) return value;
    return (value * mult).ceil() - 1;
  }

  int _calcBaseStat(String stat, int jsonStat, {bool forceMega = false}) {
    final beforeMega = jsonStat + _potentialBonus(stat) + _exRoleBonus(stat);
    final mult = _formStatMult(stat, forceMega: forceMega);
    return _applyFormMultiplier(
      beforeMega,
      mult,
      stat,
      useExactMegaRatio: _megaActive || forceMega,
    );
  }

  int _calcBeforeStageStat(
    String stat,
    int jsonStat, {
    bool forceMega = false,
  }) {
    final rawBase = jsonStat + _potentialBonus(stat) + _exRoleBonus(stat);
    final mult = _formStatMult(stat, forceMega: forceMega);
    final modifiedBase = _applyFormMultiplier(
      rawBase + (_gear[stat] ?? 0),
      mult,
      stat,
      useExactMegaRatio: _megaActive || forceMega,
    );
    return modifiedBase + _gridStatBonus(stat);
  }

  int _calcTotalStat(
    String stat,
    int jsonStat,
    int stage, {
    bool forceMega = false,
  }) {
    final beforeStage = _calcBeforeStageStat(
      stat,
      jsonStat,
      forceMega: forceMega,
    );
    return floorToInt(
      beforeStage * statVariation(stage, isSpeed: stat == 'spe'),
    );
  }

  Widget _mitigationCell(int value, ValueChanged<int> onChanged) {
    return Center(
      child: DropdownButton<int>(
        value: value,
        isDense: true,
        underline: const SizedBox(),
        style: TextStyle(
          fontSize: 10,
          fontWeight: FontWeight.w600,
          color: value > 0 ? Colors.orange.shade800 : Colors.black,
        ),
        items: [
          for (int i = 0; i <= 9; i++)
            DropdownMenuItem(value: i, child: Text('$i')),
        ],
        onChanged: (v) => onChanged(v!),
      ),
    );
  }

  Widget _stageCell(int value, ValueChanged<int> onChanged) {
    return Center(
      child: DropdownButton<int>(
        value: value,
        isDense: true,
        underline: const SizedBox(),
        style: TextStyle(
          fontSize: 10,
          fontWeight: FontWeight.w600,
          color: value > 0
              ? Colors.blue
              : value < 0
              ? Colors.red
              : Colors.black,
        ),
        items: [
          for (int i = -6; i <= 6; i++)
            DropdownMenuItem(value: i, child: Text('$i')),
        ],
        onChanged: (v) => onChanged(v!),
      ),
    );
  }

  Widget _calcFormTab(String label, int index, {Color? color}) {
    final selected = _calcFormIndex == index;
    final tabColor = color ?? Theme.of(context).colorScheme.primary;
    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() => _calcFormIndex = index),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(
            color: selected ? tabColor : Colors.transparent,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: tabColor, width: 1.5),
          ),
          alignment: Alignment.center,
          child: Text(
            label,
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w700,
              color: selected
                  ? Colors.white
                  : Theme.of(context).colorScheme.onSurface,
            ),
          ),
        ),
      ),
    );
  }

  int _gridStatBonus(String statName) {
    final mapping = {
      'hp': 'HP',
      'atk': 'Attack',
      'def': 'Defense',
      'spa': 'Sp. Atk',
      'spd': 'Sp. Def',
      'spe': 'Speed',
    };
    final prefix = mapping[statName] ?? '';
    if (prefix.isEmpty) return 0;
    int total = 0;
    for (final cell in widget.pair.cells) {
      if (!widget.activeCells.contains(cell.cellNumber)) continue;
      final t = cell.title.trim();
      if (t.startsWith(prefix)) {
        final numStr = t.substring(prefix.length).trim();
        final val = int.tryParse(numStr);
        if (val != null) total += val;
      }
    }
    return total;
  }

  int _gridPowerBonus(String moveName) {
    int total = 0;
    final prefix = '$moveName: Power ';
    for (final cell in widget.pair.cells) {
      if (!widget.activeCells.contains(cell.cellNumber)) continue;
      if (!cell.title.startsWith(prefix)) continue;
      final val = int.tryParse(cell.title.substring(prefix.length).trim());
      if (val != null) total += val;
    }
    return total;
  }

  int _totalBp(MoveData move) {
    final base = int.tryParse(_scaledPower(move.power)) ?? 0;
    final grid = _gridPowerBonus(move.name);
    final isTeraMove =
        widget.pair.teraMove != null && move.name == widget.pair.teraMove!.name;
    final tera = _teraActive && widget.pair.hasTera;
    final teraBonus =
        tera &&
        !move.isSync &&
        !isTeraMove &&
        move.type.toLowerCase() == widget.pair.type.toLowerCase();
    final afterTera = teraBonus ? (base * 1.5).floor() : base;
    final afterSyncTech = move.isSync && _syncTechExBoost
        ? (base * 1.5).floor()
        : afterTera;
    final isPhysical = move.category.toLowerCase() == 'physical';
    final boostRank = move.isSync
        ? 0
        : (isPhysical ? _physicalBoostNext : _specialBoostNext);
    final syncSkill = move.isSync ? _syncMoveBoostNext * 0.1 : 0.0;
    final masterPassiveSkill = _masterPassivePowerUp(move);
    final inner =
        ((afterSyncTech + grid) *
                (1 + syncSkill + masterPassiveSkill + boostRank * 0.4))
            .floor();
    return inner;
  }

  static const _statusLabels = {
    'burned': '🔥 Burned',
    'paralyzed': '⚡ Paralyzed',
    'frozen': '🧊 Frozen',
    'asleep': '💤 Asleep',
    'poisoned': '☠️ Poisoned',
    'badly poisoned': '☠️ Badly Pois.',
    'confused': '💫 Confused',
    'flinching': '😵 Flinching',
    'trapped': '🕸️ Trapped',
    'restrained': '⛓️ Restrained',
  };
  static const _statusColors = {
    'burned': Color(0xFFE74C3C),
    'paralyzed': Color(0xFFF39C12),
    'frozen': Color(0xFF3498DB),
    'asleep': Color(0xFF8E44AD),
    'poisoned': Color(0xFF9B59B6),
    'badly poisoned': Color(0xFF6C3483),
    'confused': Color(0xFFE91E63),
    'flinching': Color(0xFF795548),
    'trapped': Color(0xFF607D8B),
    'restrained': Color(0xFF455A64),
  };
  String _statusLabel(String key) => _statusLabels[key] ?? key;
  Color _statusColor(String key) => _statusColors[key] ?? Colors.grey;

  @override
  Widget build(BuildContext context) {
    final pair = widget.pair;
    final validStars = availableStarLevels(pair.rarity, pair.hasEx);
    if (!validStars.contains(_starLevel)) _starLevel = validStars.last;
    final levels = pair.stats.keys.toList()
      ..sort((a, b) => int.parse(a).compareTo(int.parse(b)));
    if (levels.isNotEmpty && !levels.contains(_selectedLevel))
      _selectedLevel = levels.last;
    final baseStats = pair.stats[_selectedLevel] ?? {};
    final currentStats = baseStats;

    final isTeraActive = _teraActive;
    final isVariation =
        _calcFormIndex > 0 && _calcFormIndex <= pair.variations.length;
    final activeVariation = isVariation
        ? pair.variations[_calcFormIndex - 1]
        : null;

    // Build display moves based on active form
    List<MoveData> baseMoves;
    if (isVariation && activeVariation != null) {
      baseMoves = activeVariation.applyTo(pair.moves);
    } else {
      baseMoves = pair.moves;
    }
    final displayMoves = <MoveData>[
      ...baseMoves,
      if (isTeraActive && pair.teraMove != null) pair.teraMove!,
    ].where((move) => move.power.isNotEmpty && move.power != '--').toList();
    final masterPassives = _masterPassives;

    final labelStyle = TextStyle(
      fontSize: 11,
      color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.6),
    );

    final configWidgets = <Widget>[
      // --- Level selector ---
      Row(
        children: [
          Text('Level: ', style: labelStyle),
          if (levels.isNotEmpty)
            DropdownButton<String>(
              value: _selectedLevel,
              isDense: true,
              items: [
                for (final lv in levels)
                  DropdownMenuItem(
                    value: lv,
                    child: Text(
                      'Lv. $lv',
                      style: const TextStyle(fontSize: 12),
                    ),
                  ),
              ],
              onChanged: (v) => setState(() => _selectedLevel = v!),
            )
          else
            Text('No data', style: labelStyle),
        ],
      ),
      const SizedBox(height: 6),

      // --- Star Level / EX / EX Role ---
      Row(
        children: [
          DropdownButton<String>(
            value: _starLevel,
            isDense: true,
            underline: const SizedBox(),
            style: const TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w600,
              color: Colors.black,
            ),
            items: [
              for (final sl in availableStarLevels(pair.rarity, pair.hasEx))
                DropdownMenuItem(value: sl, child: Text(sl)),
            ],
            onChanged: (v) => setState(() => _starLevel = v!),
          ),
          if (pair.hasEx && pair.exRole.isNotEmpty) ...[
            const SizedBox(width: 6),
            FilterChip(
              label: Text(
                'EX Role (${pair.exRole})',
                style: TextStyle(
                  fontSize: 11,
                  color: _hasExRole ? Colors.white : null,
                ),
              ),
              selected: _hasExRole,
              showCheckmark: false,
              onSelected: (v) => setState(() {
                _hasExRole = v;
              }),
              selectedColor: Colors.indigo,
              visualDensity: VisualDensity.compact,
            ),
          ],
        ],
      ),
      const SizedBox(height: 8),

      // --- Tera toggle (tab style) ---
      if (pair.hasTera ||
          pair.variations.isNotEmpty ||
          pair.megaStatMultiplier.isNotEmpty ||
          pair.megaStats.isNotEmpty)
        Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: Row(
            children: [
              _calcFormTab('Base', 0),
              for (int i = 0; i < pair.variations.length; i++) ...[
                const SizedBox(width: 6),
                _calcFormTab(
                  pair.variations[i].formName,
                  i + 1,
                  color: Colors.teal,
                ),
              ],
              if (pair.hasTera) ...[
                const SizedBox(width: 6),
                _calcFormTab(
                  'Tera',
                  pair.variations.length + 1,
                  color: const Color(0xFF6C5CE7),
                ),
              ],
              if (pair.megaStatMultiplier.isNotEmpty ||
                  pair.megaStats.isNotEmpty) ...[
                const SizedBox(width: 6),
                Builder(
                  builder: (_) {
                    int megaIdx = pair.variations.length + 1;
                    if (pair.hasTera) megaIdx++;
                    return _calcFormTab(
                      'Mega',
                      megaIdx,
                      color: Colors.deepOrange,
                    );
                  },
                ),
              ],
            ],
          ),
        ),

      Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.06),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              'Field Effects',
              style: TextStyle(
                fontWeight: FontWeight.w700,
                fontSize: 12,
                color: Theme.of(context).colorScheme.onSurface,
              ),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: Row(
                    children: [
                      FilterChip(
                        label: const Text('EX', style: TextStyle(fontSize: 11)),
                        selected: _isZoneEx,
                        showCheckmark: false,
                        onSelected: (v) => setState(() => _isZoneEx = v),
                        selectedColor: Colors.deepPurple,
                        visualDensity: VisualDensity.compact,
                      ),
                      const SizedBox(width: 4),
                      Expanded(
                        child: DropdownButton<String>(
                          value: _selectedZone,
                          isDense: true,
                          isExpanded: true,
                          underline: const SizedBox(),
                          items: [
                            for (final zone in _zoneOptions)
                              DropdownMenuItem(
                                value: zone,
                                child: Row(
                                  children: [
                                    Icon(
                                      _fieldEffectIcons[zone] ??
                                          Icons.help_outline,
                                      size: 16,
                                      color: zone.isNotEmpty
                                          ? _typeColors[_zoneBoostType[zone]
                                                    ?.toLowerCase()] ??
                                                Theme.of(
                                                  context,
                                                ).colorScheme.onSurface
                                          : Theme.of(
                                              context,
                                            ).colorScheme.onSurface,
                                    ),
                                    const SizedBox(width: 6),
                                    Text(
                                      _zoneLabel(zone),
                                      style: TextStyle(
                                        fontSize: 12,
                                        color: zone.isNotEmpty
                                            ? _typeColors[_zoneBoostType[zone]
                                                  ?.toLowerCase()]
                                            : null,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                          ],
                          onChanged: (v) =>
                              setState(() => _selectedZone = v ?? ''),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 6),
                Expanded(
                  child: Row(
                    children: [
                      FilterChip(
                        label: const Text('EX', style: TextStyle(fontSize: 11)),
                        selected: _isTerrainEx,
                        showCheckmark: false,
                        onSelected: (v) => setState(() => _isTerrainEx = v),
                        selectedColor: Colors.deepPurple,
                        visualDensity: VisualDensity.compact,
                      ),
                      const SizedBox(width: 4),
                      Expanded(
                        child: DropdownButton<String>(
                          value: _selectedTerrain,
                          isDense: true,
                          isExpanded: true,
                          underline: const SizedBox(),
                          items: [
                            for (final terrain in _terrainOptions)
                              DropdownMenuItem(
                                value: terrain,
                                child: Row(
                                  children: [
                                    Icon(
                                      _fieldEffectIcons[terrain] ??
                                          Icons.help_outline,
                                      size: 16,
                                      color: terrain.isNotEmpty
                                          ? _typeColors[_terrainBoostType[terrain]
                                                    ?.toLowerCase()] ??
                                                Theme.of(
                                                  context,
                                                ).colorScheme.onSurface
                                          : Theme.of(
                                              context,
                                            ).colorScheme.onSurface,
                                    ),
                                    const SizedBox(width: 6),
                                    Text(
                                      _terrainLabel(terrain),
                                      style: TextStyle(
                                        fontSize: 12,
                                        color: terrain.isNotEmpty
                                            ? _typeColors[_terrainBoostType[terrain]
                                                  ?.toLowerCase()]
                                            : null,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                          ],
                          onChanged: (v) =>
                              setState(() => _selectedTerrain = v ?? ''),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 6),
                Expanded(
                  child: Row(
                    children: [
                      FilterChip(
                        label: const Text('EX', style: TextStyle(fontSize: 11)),
                        selected: _isWeatherEx,
                        showCheckmark: false,
                        onSelected: (v) => setState(() => _isWeatherEx = v),
                        selectedColor: Colors.deepPurple,
                        visualDensity: VisualDensity.compact,
                      ),
                      const SizedBox(width: 4),
                      Expanded(
                        child: DropdownButton<String>(
                          value: _selectedWeather,
                          isDense: true,
                          isExpanded: true,
                          underline: const SizedBox(),
                          items: [
                            for (final weather in _weatherOptions)
                              DropdownMenuItem(
                                value: weather,
                                child: Row(
                                  children: [
                                    Icon(
                                      _fieldEffectIcons[weather] ??
                                          Icons.help_outline,
                                      size: 16,
                                      color: weather.isNotEmpty
                                          ? _typeColors[_weatherBoostType[weather]
                                                    ?.toLowerCase()] ??
                                                Theme.of(
                                                  context,
                                                ).colorScheme.onSurface
                                          : Theme.of(
                                              context,
                                            ).colorScheme.onSurface,
                                    ),
                                    const SizedBox(width: 6),
                                    Text(
                                      _weatherLabel(weather),
                                      style: TextStyle(
                                        fontSize: 12,
                                        color: weather.isNotEmpty
                                            ? _typeColors[_weatherBoostType[weather]
                                                  ?.toLowerCase()]
                                            : null,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                          ],
                          onChanged: (v) =>
                              setState(() => _selectedWeather = v ?? ''),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
      const SizedBox(height: 8),

      // --- Ally section title ---
      Text(
        'Ally',
        style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13),
      ),
      const SizedBox(height: 4),

      // --- Stats table (horizontal: header, base, grid, gear, before stage, stage, total) ---
      if (currentStats.isNotEmpty)
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: Theme.of(
              context,
            ).colorScheme.primary.withValues(alpha: 0.06),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Table(
            defaultVerticalAlignment: TableCellVerticalAlignment.middle,
            columnWidths: {
              0: const FixedColumnWidth(40),
              for (int i = 0; i < _statLabels.length; i++)
                i + 1: const FlexColumnWidth(),
            },
            children: [
              TableRow(
                children: [
                  const SizedBox(),
                  for (final s in _statLabels)
                    Center(
                      child: Text(
                        _playerStatNames[s]!,
                        style: const TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                ],
              ),
              TableRow(
                children: [
                  Text('Base', style: labelStyle),
                  for (final s in _statLabels)
                    Center(
                      child: Text(
                        '${_calcBaseStat(s, currentStats[s] ?? 0)}',
                        style: const TextStyle(fontSize: 11),
                      ),
                    ),
                ],
              ),
              TableRow(
                children: [
                  Text('Grid', style: labelStyle),
                  for (final s in _statLabels)
                    Builder(
                      builder: (_) {
                        final g = _gridStatBonus(s);
                        return Center(
                          child: Text(
                            g > 0 ? '+$g' : '-',
                            style: TextStyle(
                              fontSize: 11,
                              color: g > 0
                                  ? Theme.of(context).colorScheme.primary
                                  : null,
                            ),
                          ),
                        );
                      },
                    ),
                ],
              ),
              TableRow(
                children: [
                  Text('Gear', style: labelStyle),
                  for (final s in _statLabels)
                    Padding(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 2,
                        vertical: 2,
                      ),
                      child: SizedBox(
                        height: 24,
                        child: TextField(
                          controller: _gearControllers[s],
                          textAlign: TextAlign.center,
                          style: const TextStyle(fontSize: 11),
                          decoration: const InputDecoration(
                            isDense: true,
                            contentPadding: EdgeInsets.symmetric(
                              horizontal: 2,
                              vertical: 4,
                            ),
                            border: OutlineInputBorder(),
                          ),
                          keyboardType: TextInputType.number,
                          onChanged: (v) =>
                              setState(() => _gear[s] = int.tryParse(v) ?? 0),
                        ),
                      ),
                    ),
                ],
              ),
              TableRow(
                children: [
                  Text('Before Stage', style: labelStyle),
                  for (final s in _statLabels)
                    Center(
                      child: Text(
                        '${_calcBeforeStageStat(s, currentStats[s] ?? 0)}',
                        style: const TextStyle(fontSize: 11),
                      ),
                    ),
                ],
              ),
              // Player stage row
              TableRow(
                children: [
                  Text('Stage', style: labelStyle),
                  Padding(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 2,
                      vertical: 2,
                    ),
                    child: SizedBox(
                      height: 24,
                      child: TextField(
                        controller: _playerHpPercentController,
                        textAlign: TextAlign.center,
                        style: const TextStyle(fontSize: 11),
                        decoration: const InputDecoration(
                          isDense: true,
                          contentPadding: EdgeInsets.symmetric(
                            horizontal: 2,
                            vertical: 4,
                          ),
                          border: OutlineInputBorder(),
                          suffixText: '%',
                          suffixStyle: TextStyle(fontSize: 9),
                        ),
                        keyboardType: TextInputType.number,
                        onChanged: (v) => setState(
                          () => _playerHpPercent = (int.tryParse(v) ?? 100)
                              .clamp(0, 100),
                        ),
                      ),
                    ),
                  ),
                  for (final s in _statLabels.skip(1))
                    _stageCell(
                      _playerStages[s] ?? 0,
                      (v) => setState(() => _playerStages[s] = v),
                    ),
                ],
              ),
              TableRow(
                children: [
                  const Text(
                    'Total',
                    style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700),
                  ),
                  Center(
                    child: Builder(
                      builder: (_) {
                        final total =
                            (_calcBeforeStageStat(
                                      'hp',
                                      currentStats['hp'] ?? 0,
                                    ) *
                                    _playerHpPercent /
                                    100)
                                .round();
                        return Text(
                          '$total',
                          style: const TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w700,
                          ),
                        );
                      },
                    ),
                  ),
                  for (final s in _statLabels.skip(1))
                    Builder(
                      builder: (_) {
                        final total = _calcTotalStat(
                          s,
                          currentStats[s] ?? 0,
                          _playerStages[s] ?? 0,
                        );
                        return Center(
                          child: Text(
                            '$total',
                            style: const TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        );
                      },
                    ),
                ],
              ),
            ],
          ),
        ),
      const SizedBox(height: 6),
      SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          children: [
            Text('Acc: ', style: labelStyle),
            _stageCell(
              _playerStages['acc'] ?? 0,
              (v) => setState(() => _playerStages['acc'] = v),
            ),
            const SizedBox(width: 8),
            Text('Eva: ', style: labelStyle),
            _stageCell(
              _playerStages['eva'] ?? 0,
              (v) => setState(() => _playerStages['eva'] = v),
            ),
            const SizedBox(width: 8),
            Text('Crit: ', style: labelStyle),
            DropdownButton<int>(
              value: _playerStages['crit'] ?? 0,
              isDense: true,
              underline: const SizedBox(),
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w600,
                color: (_playerStages['crit'] ?? 0) > 0
                    ? Colors.blue
                    : Colors.black,
              ),
              items: [
                for (int i = 0; i <= 3; i++)
                  DropdownMenuItem(value: i, child: Text('$i')),
              ],
              onChanged: (v) => setState(() => _playerStages['crit'] = v!),
            ),
            const SizedBox(width: 8),
            Text('Sync Buffs: ', style: labelStyle),
            SizedBox(
              width: 40,
              height: 24,
              child: TextField(
                controller: _playerSyncBoostsController,
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 11),
                decoration: const InputDecoration(
                  isDense: true,
                  contentPadding: EdgeInsets.symmetric(
                    horizontal: 2,
                    vertical: 4,
                  ),
                  border: OutlineInputBorder(),
                ),
                keyboardType: TextInputType.number,
                onChanged: (v) =>
                    setState(() => _playerSyncBoosts = int.tryParse(v) ?? 0),
              ),
            ),
            const SizedBox(width: 4),
            if (_megaActive) ...[
              const SizedBox(width: 8),
              Text(
                'Mega: +${_megaSyncBaseBoosts} ',
                style: TextStyle(fontSize: 11, color: Colors.blueGrey),
              ),
            ],
            Text(
              '×${(1 + _effectivePlayerSyncBoosts * 0.5).toStringAsFixed(1)}',
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w600,
                color: _effectivePlayerSyncBoosts > 0 ? Colors.blue : null,
              ),
            ),
            const SizedBox(width: 8),
            Text('Status Cond: ', style: labelStyle),
            DropdownButton<String>(
              value: _playerStatusCondition,
              isDense: true,
              style: TextStyle(
                fontSize: 12,
                color: _playerStatusCondition.isNotEmpty
                    ? _statusColor(_playerStatusCondition)
                    : Colors.black,
              ),
              items: [
                const DropdownMenuItem(
                  value: '',
                  child: Text('None', style: TextStyle(fontSize: 12)),
                ),
                for (final s in [
                  'burned',
                  'paralyzed',
                  'frozen',
                  'asleep',
                  'poisoned',
                  'badly poisoned',
                ])
                  DropdownMenuItem(
                    value: s,
                    child: Text(
                      _statusLabel(s),
                      style: TextStyle(fontSize: 12, color: _statusColor(s)),
                    ),
                  ),
              ],
              onChanged: (v) => setState(() => _playerStatusCondition = v!),
            ),
          ],
        ),
      ),
      const SizedBox(height: 6),

      // --- Circles ---
      Text(
        'Circles',
        style: TextStyle(
          fontWeight: FontWeight.w700,
          fontSize: 12,
          color: Theme.of(context).colorScheme.onSurface,
        ),
      ),
      const SizedBox(height: 4),
      Wrap(
        spacing: 6,
        runSpacing: 4,
        children: [
          for (final region in _circleRegions)
            Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  region,
                  style: const TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 2),
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    for (final kind in ['physical', 'special', 'defensive'])
                      GestureDetector(
                        onTap: () => setState(
                          () => _circleActive[region]![kind] =
                              !_circleActive[region]![kind]!,
                        ),
                        child: Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 1),
                          child: Opacity(
                            opacity: _circleActive[region]![kind]! ? 1.0 : 0.3,
                            child: Image.asset(
                              kind == 'physical'
                                  ? 'assets/pomatools.github.io-master/assets/img/battle/CATE_001.png'
                                  : kind == 'special'
                                  ? 'assets/pomatools.github.io-master/assets/img/battle/CATE_002.png'
                                  : 'assets/pomatools.github.io-master/assets/img/battle/CATE_004.png',
                              width: 16,
                              height: 16,
                            ),
                          ),
                        ),
                      ),
                  ],
                ),
                SizedBox(
                  height: 24,
                  child: DropdownButton<int>(
                    value: _circleAllyCount[region]!,
                    isDense: true,
                    underline: const SizedBox(),
                    style: const TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                      color: Colors.black,
                    ),
                    items: [
                      for (int j = 0; j <= 3; j++)
                        DropdownMenuItem(value: j, child: Text('$j')),
                    ],
                    onChanged: (v) =>
                        setState(() => _circleAllyCount[region] = v!),
                  ),
                ),
              ],
            ),
        ],
      ),
      Builder(
        builder: (_) {
          final active = _activeCircles();
          if (active.isEmpty) return const SizedBox();
          final offPhys = calcCircleOffenseMult(active, true);
          final offSpec = calcCircleOffenseMult(active, false);
          final defPhys = calcCircleDefenseMult(active, true);
          final defSpec = calcCircleDefenseMult(active, false);
          return Padding(
            padding: const EdgeInsets.only(top: 2),
            child: Wrap(
              spacing: 12,
              children: [
                if (offPhys != 1.0)
                  Text(
                    'Phys \u00d7${offPhys.toStringAsFixed(3)}',
                    style: TextStyle(
                      fontSize: 10,
                      color: Colors.red.shade700,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                if (offSpec != 1.0)
                  Text(
                    'Spec \u00d7${offSpec.toStringAsFixed(3)}',
                    style: TextStyle(
                      fontSize: 10,
                      color: Colors.blue.shade700,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                if (defPhys != 1.0)
                  Text(
                    'Phys DR \u00d7${defPhys.toStringAsFixed(3)}',
                    style: TextStyle(
                      fontSize: 10,
                      color: Colors.green.shade700,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                if (defSpec != 1.0)
                  Text(
                    'Spec DR \u00d7${defSpec.toStringAsFixed(3)}',
                    style: TextStyle(
                      fontSize: 10,
                      color: Colors.green.shade700,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
              ],
            ),
          );
        },
      ),
      const SizedBox(height: 6),

      if (masterPassives.isNotEmpty) ...[
        Text(
          'Master Passives',
          style: TextStyle(
            fontWeight: FontWeight.w700,
            fontSize: 12,
            color: Theme.of(context).colorScheme.onSurface,
          ),
        ),
        const SizedBox(height: 4),
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: Colors.amber.withValues(alpha: 0.08),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              for (final passive in masterPassives) ...[
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        passive.name,
                        style: const TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                    Text(
                      '+${(passive.powerUpForAdditionalAllies(_masterPassiveAllyCount[passive.name] ?? 0) * 100).toStringAsFixed(0)}%',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        color: Colors.orange.shade800,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text('${passive.theme} allies:', style: labelStyle),
                    const SizedBox(width: 4),
                    DropdownButton<int>(
                      value: _masterPassiveAllyCount[passive.name] ?? 0,
                      isDense: true,
                      underline: const SizedBox(),
                      items: [
                        for (int i = 0; i <= 2; i++)
                          DropdownMenuItem(value: i, child: Text('+$i')),
                      ],
                      onChanged: (v) => setState(
                        () => _masterPassiveAllyCount[passive.name] = v ?? 0,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 2),
                Text(
                  passive.appliesToSync
                      ? 'Applies to ${switch (passive.category) {
                          _MasterPassiveCategory.physical => 'physical moves and sync moves',
                          _MasterPassiveCategory.special => 'special moves and sync moves',
                          _MasterPassiveCategory.any => 'moves and sync moves',
                        }}'
                      : 'Applies to ${switch (passive.category) {
                          _MasterPassiveCategory.physical => 'physical moves',
                          _MasterPassiveCategory.special => 'special moves',
                          _MasterPassiveCategory.any => 'moves',
                        }}',
                  style: labelStyle,
                ),
                if (passive != masterPassives.last) const SizedBox(height: 8),
              ],
            ],
          ),
        ),
        const SizedBox(height: 6),
      ],

      Text(
        'Enemy',
        style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13),
      ),
      const SizedBox(height: 4),
      Row(
        children: [
          Text('Weakness: ', style: labelStyle),
          DropdownButton<String>(
            value: _enemyWeakness,
            isDense: true,
            items: [
              for (final t in _weaknessTypes)
                DropdownMenuItem(
                  value: t,
                  child: Text(
                    t.isEmpty ? 'None' : t,
                    style: const TextStyle(fontSize: 12),
                  ),
                ),
            ],
            onChanged: (v) => setState(() => _enemyWeakness = v!),
          ),
        ],
      ),

      const SizedBox(height: 4),
      Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: Colors.red.withValues(alpha: 0.06),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Table(
          defaultVerticalAlignment: TableCellVerticalAlignment.middle,
          columnWidths: {
            0: const FixedColumnWidth(40),
            for (int i = 0; i < _statLabels.length; i++)
              i + 1: const FlexColumnWidth(),
          },
          children: [
            TableRow(
              children: [
                const SizedBox(),
                for (final s in _statLabels)
                  Center(
                    child: Text(
                      _enemyStatNames[s]!,
                      style: const TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
              ],
            ),
            TableRow(
              children: [
                Text('Base', style: labelStyle),
                for (final s in _statLabels)
                  Padding(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 2,
                      vertical: 2,
                    ),
                    child: SizedBox(
                      height: 24,
                      child: TextField(
                        controller: _enemyControllers[s],
                        textAlign: TextAlign.center,
                        style: const TextStyle(fontSize: 11),
                        decoration: const InputDecoration(
                          isDense: true,
                          contentPadding: EdgeInsets.symmetric(
                            horizontal: 2,
                            vertical: 4,
                          ),
                          border: OutlineInputBorder(),
                        ),
                        keyboardType: TextInputType.number,
                        onChanged: (v) =>
                            setState(() => _enemy[s] = int.tryParse(v) ?? 0),
                      ),
                    ),
                  ),
              ],
            ),
            TableRow(
              children: [
                Text('Stage', style: labelStyle),
                Padding(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 2,
                    vertical: 2,
                  ),
                  child: SizedBox(
                    height: 24,
                    child: TextField(
                      controller: _enemyHpPercentController,
                      textAlign: TextAlign.center,
                      style: const TextStyle(fontSize: 11),
                      decoration: const InputDecoration(
                        isDense: true,
                        contentPadding: EdgeInsets.symmetric(
                          horizontal: 2,
                          vertical: 4,
                        ),
                        border: OutlineInputBorder(),
                        suffixText: '%',
                        suffixStyle: TextStyle(fontSize: 9),
                      ),
                      keyboardType: TextInputType.number,
                      onChanged: (v) => setState(
                        () => _enemyHpPercent = (int.tryParse(v) ?? 100).clamp(
                          0,
                          100,
                        ),
                      ),
                    ),
                  ),
                ),
                for (final s in _statLabels.skip(1))
                  _stageCell(
                    _enemyStages[s] ?? 0,
                    (v) => setState(() => _enemyStages[s] = v),
                  ),
              ],
            ),
            TableRow(
              children: [
                Text('Mitig.', style: labelStyle),
                const Center(child: Text('-', style: TextStyle(fontSize: 10))),
                for (final s in _statLabels.skip(1))
                  _mitigationCell(
                    _enemyMitigations[s] ?? 0,
                    (v) => setState(() => _enemyMitigations[s] = v),
                  ),
              ],
            ),
          ],
        ),
      ),
      const SizedBox(height: 6),
      SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          children: [
            Text('Acc: ', style: labelStyle),
            _stageCell(
              _enemyStages['acc'] ?? 0,
              (v) => setState(() => _enemyStages['acc'] = v),
            ),
            const SizedBox(width: 8),
            Text('Eva: ', style: labelStyle),
            _stageCell(
              _enemyStages['eva'] ?? 0,
              (v) => setState(() => _enemyStages['eva'] = v),
            ),
            const SizedBox(width: 8),
            Text('Sync Buffs: ', style: labelStyle),
            SizedBox(
              width: 40,
              height: 24,
              child: TextField(
                controller: _enemySyncBoostsController,
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 11),
                decoration: const InputDecoration(
                  isDense: true,
                  contentPadding: EdgeInsets.symmetric(
                    horizontal: 2,
                    vertical: 4,
                  ),
                  border: OutlineInputBorder(),
                ),
                keyboardType: TextInputType.number,
                onChanged: (v) =>
                    setState(() => _enemySyncBoosts = int.tryParse(v) ?? 0),
              ),
            ),
            const SizedBox(width: 4),
            Text(
              '×${(1 + _enemySyncBoosts * 0.5).toStringAsFixed(1)}',
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w600,
                color: _enemySyncBoosts > 0 ? Colors.red : null,
              ),
            ),
            const SizedBox(width: 8),
            Text('Status Cond: ', style: labelStyle),
            DropdownButton<String>(
              value: _enemyStatusCondition,
              isDense: true,
              style: TextStyle(
                fontSize: 12,
                color: _enemyStatusCondition.isNotEmpty
                    ? _statusColor(_enemyStatusCondition)
                    : Colors.black,
              ),
              items: [
                const DropdownMenuItem(
                  value: '',
                  child: Text('None', style: TextStyle(fontSize: 12)),
                ),
                for (final s in [
                  'burned',
                  'paralyzed',
                  'frozen',
                  'asleep',
                  'poisoned',
                  'badly poisoned',
                ])
                  DropdownMenuItem(
                    value: s,
                    child: Text(
                      _statusLabel(s),
                      style: TextStyle(fontSize: 12, color: _statusColor(s)),
                    ),
                  ),
              ],
              onChanged: (v) => setState(() => _enemyStatusCondition = v!),
            ),
          ],
        ),
      ),
      const SizedBox(height: 4),
      SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          children: [
            Text('Status Change: ', style: labelStyle),
            const SizedBox(width: 4),
            for (final entry in _enemyVolatile.entries) ...[
              FilterChip(
                label: Text(
                  _statusLabel(entry.key),
                  style: TextStyle(
                    fontSize: 10,
                    color: entry.value ? Colors.white : null,
                  ),
                ),
                selected: entry.value,
                showCheckmark: false,
                onSelected: (v) =>
                    setState(() => _enemyVolatile[entry.key] = v),
                selectedColor: _statusColor(entry.key),
                visualDensity: VisualDensity.compact,
                materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
              ),
              const SizedBox(width: 4),
            ],
          ],
        ),
      ),
      const SizedBox(height: 8),

      Row(
        children: [
          FilterChip(
            label: const Text('Phys Break', style: TextStyle(fontSize: 10)),
            selected: _physicalBreak,
            showCheckmark: false,
            onSelected: (v) => setState(() => _physicalBreak = v),
            selectedColor: Colors.red.shade700,
            visualDensity: VisualDensity.compact,
          ),
          const SizedBox(width: 4),
          FilterChip(
            label: const Text('Spec Break', style: TextStyle(fontSize: 10)),
            selected: _specialBreak,
            showCheckmark: false,
            onSelected: (v) => setState(() => _specialBreak = v),
            selectedColor: Colors.blue.shade700,
            visualDensity: VisualDensity.compact,
          ),
        ],
      ),
      const SizedBox(height: 8),

      // --- Type Rebuffs ---
      Text(
        'Type Rebuffs',
        style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13),
      ),
      const SizedBox(height: 4),
      Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: Colors.orange.withValues(alpha: 0.06),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Wrap(
          spacing: 6,
          runSpacing: 4,
          children: [
            for (final type in _allTypes.skip(1))
              _TypeRebuffDropdown(
                type: type,
                value: _typeRebuffs[type] ?? 0,
                onChanged: (v) => setState(() => _typeRebuffs[type] = v),
              ),
            _TypeRebuffDropdown(
              type: 'Stellar',
              value: _stellarRebuff,
              onChanged: (v) => setState(() => _stellarRebuff = v),
            ),
          ],
        ),
      ),
      const SizedBox(height: 10),
    ];

    final moveWidgets = <Widget>[];
    if (displayMoves.isNotEmpty) {
      moveWidgets.addAll([
        Text(
          'Moves',
          style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13),
        ),
        const SizedBox(height: 6),
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Row(
            children: [
              Text('Phys Up Next: ', style: labelStyle),
              DropdownButton<int>(
                value: _physicalBoostNext,
                isDense: true,
                underline: const SizedBox(),
                style: const TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.w600,
                  color: Colors.black,
                ),
                items: [
                  for (int i = 0; i <= 10; i++)
                    DropdownMenuItem(value: i, child: Text('$i')),
                ],
                onChanged: (v) => setState(() => _physicalBoostNext = v!),
              ),
              const SizedBox(width: 8),
              Text('Spec Up Next: ', style: labelStyle),
              DropdownButton<int>(
                value: _specialBoostNext,
                isDense: true,
                underline: const SizedBox(),
                style: const TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.w600,
                  color: Colors.black,
                ),
                items: [
                  for (int i = 0; i <= 10; i++)
                    DropdownMenuItem(value: i, child: Text('$i')),
                ],
                onChanged: (v) => setState(() => _specialBoostNext = v!),
              ),
              const SizedBox(width: 8),
              Text('Sync Up Next: ', style: labelStyle),
              DropdownButton<int>(
                value: _syncMoveBoostNext,
                isDense: true,
                underline: const SizedBox(),
                style: const TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.w600,
                  color: Colors.black,
                ),
                items: [
                  for (int i = 0; i <= 10; i++)
                    DropdownMenuItem(value: i, child: Text('$i')),
                ],
                onChanged: (v) => setState(() => _syncMoveBoostNext = v!),
              ),
              const SizedBox(width: 8),
              FilterChip(
                label: const Text('SE Up Next', style: TextStyle(fontSize: 10)),
                selected: _superEffectiveNext,
                showCheckmark: false,
                onSelected: (v) => setState(() => _superEffectiveNext = v),
                selectedColor: Colors.orange,
                visualDensity: VisualDensity.compact,
              ),
              const SizedBox(width: 8),
              FilterChip(
                label: const Text('Critical', style: TextStyle(fontSize: 10)),
                selected: _isCriticalMove,
                showCheckmark: false,
                onSelected: (v) => setState(() => _isCriticalMove = v),
                selectedColor: Colors.red,
                visualDensity: VisualDensity.compact,
              ),
              const SizedBox(width: 8),
              Text('Targets: ', style: labelStyle),
              DropdownButton<int>(
                value: _targetCount,
                isDense: true,
                underline: const SizedBox(),
                style: const TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.w600,
                  color: Colors.black,
                ),
                items: const [
                  DropdownMenuItem(value: 1, child: Text('1')),
                  DropdownMenuItem(value: 2, child: Text('2')),
                  DropdownMenuItem(value: 3, child: Text('3')),
                ],
                onChanged: (v) => setState(() => _targetCount = v!),
              ),
            ],
          ),
        ),
        const SizedBox(height: 6),
        for (final move in displayMoves)
          Builder(
            builder: (_) {
              final hasPower = move.power.isNotEmpty && move.power != '--';
              final bp = hasPower ? _totalBp(move) : null;
              final isPhysical = move.category.toLowerCase() == 'physical';
              final atkKey = isPhysical ? 'atk' : 'spa';
              final forceMega = _usesMegaSyncStats(move);
              final defStat = _enemy[isPhysical ? 'def' : 'spd'] ?? 100;
              List<int>? rolls;
              if (bp != null && bp > 0) {
                final atkTotal = calcStat(
                  StatInput(
                    baseStat: _calcBeforeStageStat(
                      atkKey,
                      currentStats[atkKey] ?? 0,
                      forceMega: forceMega,
                    ),
                    stage: _playerStages[atkKey] ?? 0,
                  ),
                );
                final defKey = isPhysical ? 'def' : 'spd';
                final enemyDefTotal = calcStat(
                  StatInput(
                    baseStat: defStat,
                    stage: _enemyStages[defKey] ?? 0,
                    mitigation: _enemyMitigations[defKey] ?? 0,
                  ),
                );
                final isSE =
                    _enemyWeakness.isNotEmpty &&
                    move.type.toLowerCase() == _enemyWeakness.toLowerCase();
                final moveType = move.type.isNotEmpty
                    ? move.type[0].toUpperCase() +
                          move.type.substring(1).toLowerCase()
                    : '';
                final rebuff = _typeRebuffs[moveType] ?? 0;
                final stellarRebuff = moveType == 'Stellar'
                    ? _stellarRebuff
                    : 0;
                final zoneBoost =
                    _selectedZone.isNotEmpty &&
                    _zoneBoostType[_selectedZone]?.toLowerCase() ==
                        moveType.toLowerCase();
                final terrainBoost =
                    _selectedTerrain.isNotEmpty &&
                    _terrainBoostType[_selectedTerrain]?.toLowerCase() ==
                        moveType.toLowerCase();
                final weatherBoost =
                    _selectedWeather.isNotEmpty &&
                    _weatherBoostType[_selectedWeather]?.toLowerCase() ==
                        moveType.toLowerCase();
                final result = calcDamage(
                  moveInput: MovePowerInput(
                    basePower: bp,
                    moveLevel: 1,
                    gridPower: 0,
                    boostRank: 0,
                    skillPowerUps: 0,
                  ),
                  attackerInput: StatInput(baseStat: atkTotal),
                  defenderStat: enemyDefTotal,
                  conditions: BattleConditions(
                    syncBoosts: _effectivePlayerSyncBoosts,
                    isCritical: _isCriticalMove,
                    isSuperEffective: isSE,
                    hasSENext: _superEffectiveNext,
                    typeRebuff: rebuff,
                    stellarRebuff: stellarRebuff,
                    zoneBoost: zoneBoost,
                    zoneEx: _isZoneEx,
                    terrainBoost: terrainBoost,
                    terrainEx: _isTerrainEx,
                    weatherBoost: weatherBoost,
                    weatherEx: _isWeatherEx,
                    physicalBreak: isPhysical && _physicalBreak && !move.isSync,
                    specialBreak: !isPhysical && _specialBreak && !move.isSync,
                    isPhysicalMove: isPhysical,
                    targetCount: _targetCount,
                    circles: _activeCircles(),
                  ),
                );
                rolls = result.rolls;
              }
              final isTeraMove =
                  pair.teraMove != null && move.name == pair.teraMove!.name;
              final moveTeraBoost =
                  isTeraActive &&
                  !move.isSync &&
                  !isTeraMove &&
                  move.type.toLowerCase() == pair.type.toLowerCase();
              final tooltipLines = <String>[];
              if (bp != null) {
                tooltipLines.add('Base Power: ${_scaledPower(move.power)}');
                if (move.isSync && _syncTechExBoost) {
                  tooltipLines.add('6EX Tech Sync Move ×1.5');
                }
                if (moveTeraBoost) tooltipLines.add('Tera Boost ×1.5');
                final gp = _gridPowerBonus(move.name);
                if (gp > 0) tooltipLines.add('Grid Power: +$gp (additive)');
                final masterPassiveSkill = _masterPassivePowerUp(move);
                if (masterPassiveSkill > 0) {
                  tooltipLines.add(
                    'Master Passive +${(masterPassiveSkill * 100).toStringAsFixed(0)}%',
                  );
                }
                final boostRank = move.isSync
                    ? 0
                    : (isPhysical ? _physicalBoostNext : _specialBoostNext);
                if (boostRank > 0)
                  tooltipLines.add(
                    '${isPhysical ? 'Phys' : 'Spec'} Up Next +${(boostRank * 40).toStringAsFixed(0)}%',
                  );
                if (move.isSync && _syncMoveBoostNext > 0)
                  tooltipLines.add(
                    'Sync Up Next +${(_syncMoveBoostNext * 10).toStringAsFixed(0)}%',
                  );
              }
              final hasBpMod =
                  moveTeraBoost ||
                  _gridPowerBonus(move.name) > 0 ||
                  _masterPassivePowerUp(move) > 0 ||
                  (move.isSync
                      ? _syncMoveBoostNext > 0
                      : (isPhysical
                            ? _physicalBoostNext > 0
                            : _specialBoostNext > 0));
              final baseBpVal = int.tryParse(_scaledPower(move.power));
              return _CalcMoveCard(
                move: move,
                totalBp: bp,
                baseBp: baseBpVal,
                hasBpMod: hasBpMod,
                teraBoost: moveTeraBoost,
                atkStat: rolls != null
                    ? calcStat(
                        StatInput(
                          baseStat: _calcBeforeStageStat(
                            atkKey,
                            currentStats[atkKey] ?? 0,
                            forceMega: forceMega,
                          ),
                          stage: _playerStages[atkKey] ?? 0,
                        ),
                      )
                    : null,
                rolls: rolls,
                enemyHp: ((_enemy['hp'] ?? 1) * _enemyHpPercent / 100).round(),
                tooltipText: tooltipLines.join('\n'),
              );
            },
          ),
      ]);
    }

    if (widget.expanded) {
      return Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: configWidgets,
              ),
            ),
          ),
          const VerticalDivider(width: 1),
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.only(left: 8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: moveWidgets,
              ),
            ),
          ),
        ],
      );
    }

    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [...configWidgets, ...moveWidgets],
      ),
    );
  }
}

class _TypeRebuffDropdown extends StatelessWidget {
  const _TypeRebuffDropdown({
    required this.type,
    required this.value,
    required this.onChanged,
  });
  final String type;
  final int value;
  final ValueChanged<int> onChanged;

  @override
  Widget build(BuildContext context) {
    final color = _typeColors[type.toLowerCase()] ?? Colors.grey;
    final iconPath = _typeIcons[type.toLowerCase()];
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
      decoration: BoxDecoration(
        color: value != 0
            ? color.withValues(alpha: 0.2)
            : color.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(
          color: value != 0 ? color : color.withValues(alpha: 0.3),
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (iconPath != null)
            Image.asset(iconPath, width: 18, height: 18)
          else
            Text(
              type,
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w600,
                color: color,
              ),
            ),
          const SizedBox(width: 2),
          DropdownButton<int>(
            value: value,
            isDense: true,
            underline: const SizedBox(),
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w700,
              color: value < 0 ? Colors.green.shade800 : Colors.black,
            ),
            items: [
              for (int i = 0; i >= -3; i--)
                DropdownMenuItem(value: i, child: Text('$i')),
            ],
            onChanged: (v) => onChanged(v!),
          ),
        ],
      ),
    );
  }
}

class _CalcMoveCard extends StatelessWidget {
  const _CalcMoveCard({
    required this.move,
    this.totalBp,
    this.baseBp,
    this.hasBpMod = false,
    this.teraBoost = false,
    this.atkStat,
    this.rolls,
    this.enemyHp = 1,
    this.tooltipText = '',
  });
  final MoveData move;
  final int? totalBp;
  final int? baseBp;
  final bool hasBpMod;
  final bool teraBoost;
  final int? atkStat;
  final List<int>? rolls;
  final int enemyHp;
  final String tooltipText;

  @override
  Widget build(BuildContext context) {
    String? pctLabel;
    if (rolls != null && rolls!.isNotEmpty && enemyHp > 0) {
      final minPct = (rolls!.first / enemyHp * 100).toStringAsFixed(1);
      final maxPct = (rolls!.last / enemyHp * 100).toStringAsFixed(1);
      pctLabel = '$minPct-$maxPct%';
    }
    final typeColor = _typeColors[move.type.toLowerCase()];
    final hasBp = totalBp != null;
    return Tooltip(
      message: tooltipText,
      waitDuration: const Duration(milliseconds: 300),
      child: Container(
        margin: const EdgeInsets.only(bottom: 6),
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color:
              typeColor?.withValues(alpha: 0.12) ??
              Theme.of(context).colorScheme.surface,
          borderRadius: BorderRadius.circular(6),
          border: Border.all(
            color: typeColor?.withValues(alpha: 0.5) ?? Colors.grey.shade300,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Row 1: Base: [name] [category] [%hp]
            Row(
              children: [
                Text(
                  '',
                  style: TextStyle(
                    fontSize: 10,
                    color: Theme.of(
                      context,
                    ).colorScheme.onSurface.withValues(alpha: 0.3),
                  ),
                ),
                if (move.isSync)
                  Padding(
                    padding: const EdgeInsets.only(right: 4),
                    child: Icon(
                      Icons.star,
                      size: 12,
                      color: Colors.purple.shade300,
                    ),
                  ),
                Expanded(
                  child: Text(
                    move.name,
                    style: const TextStyle(
                      fontWeight: FontWeight.w700,
                      fontSize: 12,
                    ),
                  ),
                ),
                if (move.category.isNotEmpty)
                  Text(
                    move.category,
                    style: TextStyle(
                      fontSize: 10,
                      color: Theme.of(
                        context,
                      ).colorScheme.onSurface.withValues(alpha: 0.5),
                    ),
                  ),
                if (pctLabel != null)
                  Padding(
                    padding: const EdgeInsets.only(left: 6),
                    child: Text(
                      pctLabel,
                      style: TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.w700,
                        color: Theme.of(context).colorScheme.primary,
                      ),
                    ),
                  ),
              ],
            ),
            // Row 2: Stat: X - Power: Y → Z
            if (hasBp)
              Padding(
                padding: const EdgeInsets.only(top: 2),
                child: Row(
                  children: [
                    if (atkStat != null)
                      Text(
                        'Stat: $atkStat - ',
                        style: TextStyle(
                          fontSize: 10,
                          color: Theme.of(
                            context,
                          ).colorScheme.onSurface.withValues(alpha: 0.6),
                        ),
                      ),
                    Text(
                      'Power: ',
                      style: TextStyle(
                        fontSize: 10,
                        color: Theme.of(
                          context,
                        ).colorScheme.onSurface.withValues(alpha: 0.6),
                      ),
                    ),
                    if (hasBpMod && baseBp != null) ...[
                      Text(
                        '$baseBp',
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.w700,
                          color: Theme.of(context).colorScheme.onSurface,
                        ),
                      ),
                      Text(
                        ' \u2192 ',
                        style: TextStyle(
                          fontSize: 10,
                          color: Theme.of(
                            context,
                          ).colorScheme.onSurface.withValues(alpha: 0.5),
                        ),
                      ),
                      Text(
                        '$totalBp',
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.w700,
                          color: teraBoost
                              ? const Color(0xFF6C5CE7)
                              : Theme.of(context).colorScheme.primary,
                        ),
                      ),
                    ] else
                      Text(
                        '$totalBp',
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.w700,
                          color: Theme.of(context).colorScheme.onSurface,
                        ),
                      ),
                  ],
                ),
              ),
            // Row 3: rolls
            if (rolls != null && rolls!.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 2),
                child: Wrap(
                  spacing: 4,
                  children: [
                    for (int i = 0; i < rolls!.length; i++)
                      Text(
                        '${rolls![i]}',
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: i == rolls!.length - 1
                              ? FontWeight.w700
                              : FontWeight.normal,
                          color: i == rolls!.length - 1
                              ? Theme.of(context).colorScheme.primary
                              : Theme.of(
                                  context,
                                ).colorScheme.onSurface.withValues(alpha: 0.6),
                        ),
                      ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class HexGridView extends StatelessWidget {
  const HexGridView({
    super.key,
    required this.cells,
    required this.pairs,
    required this.activeCells,
    required this.onToggleCell,
    required this.onSelectPair,
    required this.moveLevel,
    this.syncMoveName = '',
  });

  final List<GridCellData> cells;
  final List<SyncPairData> pairs;
  final Set<int> activeCells;
  final ValueChanged<int> onToggleCell;
  final ValueChanged<int> onSelectPair;
  final int moveLevel;
  final String syncMoveName;

  @override
  Widget build(BuildContext context) {
    if (cells.isEmpty) {
      return const Center(child: Text('This character has no grid loaded.'));
    }

    // Inject a virtual center cell at (0,0,0) if none exists.
    final allCells = cells.any((c) => c.q == 0 && c.r == 0 && c.s == 0)
        ? cells
        : [
            const GridCellData(
              cellNumber: -1,
              q: 0,
              r: 0,
              s: 0,
              energyCost: 0,
              orbCost: 0,
              title: '',
              description: '',
              colorKind: '',
            ),
            ...cells,
          ];

    const double tileRadius = 60.0;

    final coords = <int, Offset>{};
    final hexW = 1.5 * tileRadius + 1;
    final hexH = math.sqrt(3) * tileRadius - 0.5 + 1;
    for (final cell in allCells) {
      final x = hexW * cell.q;
      final y = -hexH * (cell.r + cell.q / 2.0);
      coords[cell.cellNumber] = Offset(x, y);
    }

    final cMinX = coords.values.map((o) => o.dx).reduce(math.min);
    final cMinY = coords.values.map((o) => o.dy).reduce(math.min);
    final cMaxX = coords.values.map((o) => o.dx).reduce(math.max);
    final cMaxY = coords.values.map((o) => o.dy).reduce(math.max);

    final tileW = tileRadius * 2;
    final tileH = math.sqrt(3) * tileRadius;
    final contentW = (cMaxX - cMinX) + tileW + 32;
    final contentH = (cMaxY - cMinY) + tileH + 32;

    final vController = ScrollController();
    final hController = ScrollController();

    return LayoutBuilder(
      builder: (context, viewportConstraints) {
        return Scrollbar(
          controller: hController,
          notificationPredicate: (n) => n.depth == 0,
          thumbVisibility: true,
          child: SingleChildScrollView(
            controller: hController,
            scrollDirection: Axis.horizontal,
            child: Scrollbar(
              controller: vController,
              notificationPredicate: (n) => n.depth == 0,
              thumbVisibility: true,
              child: SingleChildScrollView(
                controller: vController,
                child: SizedBox(
                  width: math.max(contentW, viewportConstraints.maxWidth),
                  height: math.max(contentH, viewportConstraints.maxHeight),
                  child: Builder(
                    builder: (context) {
                      final offsetX = math.max(
                        0.0,
                        (viewportConstraints.maxWidth - contentW) / 2,
                      );
                      final offsetY = math.max(
                        0.0,
                        (viewportConstraints.maxHeight - contentH) / 2,
                      );
                      return Stack(
                        children: [
                          for (final cell in allCells)
                            Positioned(
                              left:
                                  coords[cell.cellNumber]!.dx - cMinX + offsetX,
                              top:
                                  coords[cell.cellNumber]!.dy - cMinY + offsetY,
                              child: (cell.q == 0 && cell.r == 0 && cell.s == 0)
                                  ? GestureDetector(
                                      onTap: () => _showPairPicker(context),
                                      child: SizedBox(
                                        width: tileW,
                                        height: tileH,
                                        child: Center(
                                          child: Image.asset(
                                            'assets/img/sync_icon.png',
                                            width: tileRadius * 2,
                                            height: math.sqrt(3) * tileRadius,
                                            fit: BoxFit.contain,
                                          ),
                                        ),
                                      ),
                                    )
                                  : HoverTooltip(
                                      message: _buildCellTooltip(cell),
                                      child: Builder(
                                        builder: (_) {
                                          final colorKind =
                                              _isSyncMoveTile(cell)
                                              ? '(sync move)'
                                              : cell.colorKind;
                                          final (activeC, darkC) = _gridColors(
                                            colorKind,
                                          );
                                          return HexTile(
                                            radius: tileRadius,
                                            activeColor: activeC,
                                            darkColor: darkC,
                                            active: activeCells.contains(
                                              cell.cellNumber,
                                            ),
                                            locked: cell.moveLevel > moveLevel,
                                            label: _buildCellLabel(
                                              cell,
                                              syncMoveName: syncMoveName,
                                            ),
                                            onTap: () =>
                                                onToggleCell(cell.cellNumber),
                                          );
                                        },
                                      ),
                                    ),
                            ),
                        ],
                      );
                    },
                  ),
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  void _showPairPicker(BuildContext context) {
    showDialog(
      context: context,
      builder: (_) => _PairPickerDialog(
        pairs: pairs,
        onSelect: (index) {
          Navigator.of(context).pop();
          onSelectPair(index);
        },
      ),
    );
  }

  static String _buildCellTooltip(GridCellData cell) {
    final buffer = StringBuffer();
    if (cell.title.isNotEmpty) {
      buffer.writeln(cell.title);
    }
    if (cell.description.isNotEmpty) {
      buffer.writeln(cell.description);
    }
    buffer.writeln('⚡ ${cell.energyCost}  🔮 ${cell.orbCost}');
    return buffer.toString().trim();
  }

  static String _buildCellLabel(GridCellData cell, {String syncMoveName = ''}) {
    final title = cell.title.trim();
    if (title.isEmpty) {
      return '${cell.cellNumber}';
    }
    if (syncMoveName.isNotEmpty && title.startsWith(syncMoveName)) {
      final rest = title.substring(syncMoveName.length).trim();
      final match = RegExp(
        r':\s*Power\s+(\d+)',
        caseSensitive: false,
      ).firstMatch(rest);
      if (match != null) return 'Sync Move Power +${match.group(1)}';
    }
    return title
        .replaceAllMapped(
          RegExp(r'Move Gauge Refresh\s+(\d+)', caseSensitive: false),
          (match) => 'MGR${match.group(1)}',
        )
        .replaceAllMapped(
          RegExp(r'MP Refresh\s+(\d+)', caseSensitive: false),
          (match) => 'MPR${match.group(1)}',
        );
  }

  static const _tileColors = <String, (Color active, Color dark)>{
    'stat': (Color(0xFF4A90D9), Color(0xFF18529C)),
    'move boost': (Color(0xFF2ECC71), Color(0xFF056E50)),
    'move effect': (Color(0xFFE74C3C), Color(0xFFA7364A)),
    'sync': (Color(0xFF9B59B6), Color(0xFF432D7F)),
    'passive': (Color(0xFFF1C40F), Color(0xFF907500)),
  };

  static (Color, Color) _gridColors(String kind) {
    final n = kind.toLowerCase();
    if (n.contains('(sync move)')) return _tileColors['sync']!;
    if (n.contains('(stat)')) return _tileColors['stat']!;
    if (n.contains('(move boost)')) return _tileColors['move boost']!;
    if (n.contains('(move effect)')) return _tileColors['move effect']!;
    if (n.contains('(passive)')) return _tileColors['passive']!;
    return _tileColors['passive']!;
  }

  bool _isSyncMoveTile(GridCellData cell) {
    if (syncMoveName.isEmpty) return false;
    return cell.title.startsWith(syncMoveName);
  }
}

class _PairPickerDialog extends StatefulWidget {
  const _PairPickerDialog({required this.pairs, required this.onSelect});
  final List<SyncPairData> pairs;
  final ValueChanged<int> onSelect;
  @override
  State<_PairPickerDialog> createState() => _PairPickerDialogState();
}

class _PairPickerDialogState extends State<_PairPickerDialog> {
  String _query = '';
  bool _ascending = true;

  @override
  Widget build(BuildContext context) {
    final normalizedQuery = _query.trim().toLowerCase();
    final filtered = <int>[];
    for (int i = 0; i < widget.pairs.length; i++) {
      final p = widget.pairs[i];
      final matchesQuery =
          normalizedQuery.isEmpty ||
          p.searchTerms.any(
            (term) => term.toLowerCase().contains(normalizedQuery),
          );
      if (matchesQuery) {
        filtered.add(i);
      }
    }
    filtered.sort((a, b) {
      final cmp = widget.pairs[a].displayName.compareTo(
        widget.pairs[b].displayName,
      );
      return _ascending ? cmp : -cmp;
    });

    return SimpleDialog(
      title: Row(
        children: [
          const Expanded(child: Text('Select character')),
          IconButton(
            icon: Icon(
              _ascending ? Icons.arrow_upward : Icons.arrow_downward,
              size: 18,
            ),
            tooltip: _ascending ? 'A-Z' : 'Z-A',
            onPressed: () => setState(() => _ascending = !_ascending),
          ),
        ],
      ),
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: TextField(
            autofocus: true,
            decoration: const InputDecoration(
              hintText: 'Search...',
              prefixIcon: Icon(Icons.search, size: 18),
              isDense: true,
              contentPadding: EdgeInsets.symmetric(horizontal: 8, vertical: 8),
              border: OutlineInputBorder(),
            ),
            style: const TextStyle(fontSize: 13),
            onChanged: (v) => setState(() => _query = v),
          ),
        ),
        const SizedBox(height: 8),
        SizedBox(
          width: 400,
          height: 450,
          child: ListView.builder(
            itemCount: filtered.length,
            itemBuilder: (context, i) {
              final index = filtered[i];
              final pair = widget.pairs[index];
              return ListTile(
                dense: true,
                title: Text(
                  pair.displayName,
                  style: const TextStyle(fontSize: 13),
                ),
                subtitle: Text(
                  [
                    if (pair.role.isNotEmpty) pair.role,
                    if (pair.type.isNotEmpty) pair.type,
                  ].join(' | '),
                  style: const TextStyle(fontSize: 11),
                ),
                onTap: () => widget.onSelect(index),
              );
            },
          ),
        ),
      ],
    );
  }
}

class HexTile extends StatelessWidget {
  const HexTile({
    super.key,
    required this.radius,
    required this.activeColor,
    required this.darkColor,
    required this.active,
    required this.label,
    required this.onTap,
    this.locked = false,
  });

  final double radius;
  final Color activeColor;
  final Color darkColor;
  final bool active;
  final String label;
  final VoidCallback onTap;
  final bool locked;

  @override
  Widget build(BuildContext context) {
    final width = radius * 2;
    final height = math.sqrt(3) * radius;
    final Color borderColor;
    final Color fillColor;
    if (locked) {
      borderColor = Color.lerp(const Color(0xFF929292), Colors.black, 0.4)!;
      fillColor = Color.lerp(const Color(0xFF929292), Colors.black, 0.5)!;
    } else if (active) {
      borderColor = Color.lerp(activeColor, Colors.black, 0.3)!;
      fillColor = activeColor;
    } else {
      final tinted = Color.lerp(const Color(0xFF929292), activeColor, 0.3)!;
      borderColor = Color.lerp(tinted, Colors.black, 0.3)!;
      fillColor = tinted;
    }
    return Listener(
      onPointerDown: (_) => onTap(),
      child: CustomPaint(
        size: Size(width, height),
        painter: HexPainter(
          borderColor: borderColor,
          fillColor: fillColor,
          borderWidth: 5.0,
        ),
        child: SizedBox(
          width: width,
          height: height,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
            child: LayoutBuilder(
              builder: (context, constraints) {
                final safeWidth = constraints.maxWidth;
                final safeHeight = constraints.maxHeight;
                final fontSize = _resolveFontSize(
                  text: label,
                  maxWidth: safeWidth,
                  maxHeight: safeHeight,
                );
                return Center(
                  child: Text(
                    label,
                    textAlign: TextAlign.center,
                    maxLines: 4,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontWeight: FontWeight.w700,
                      color: Colors.white,
                      fontSize: fontSize,
                      height: 1.05,
                      shadows: const [
                        Shadow(
                          offset: Offset(1, 1),
                          blurRadius: 2,
                          color: Colors.black,
                        ),
                        Shadow(
                          offset: Offset(-1, -1),
                          blurRadius: 2,
                          color: Colors.black,
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
        ),
      ),
    );
  }

  double _resolveFontSize({
    required String text,
    required double maxWidth,
    required double maxHeight,
  }) {
    const maxFont = 16.0;
    const minFont = 10.0;

    for (double size = maxFont; size >= minFont; size -= 0.25) {
      final painter = TextPainter(
        text: TextSpan(
          text: text,
          style: TextStyle(fontWeight: FontWeight.w700, fontSize: size),
        ),
        maxLines: 4,
        textDirection: TextDirection.ltr,
      )..layout(maxWidth: maxWidth);

      if (!painter.didExceedMaxLines && painter.height <= maxHeight) {
        return size;
      }
    }

    return minFont;
  }
}

class HoverTooltip extends StatefulWidget {
  const HoverTooltip({super.key, required this.message, required this.child});

  final String message;
  final Widget child;

  @override
  State<HoverTooltip> createState() => _HoverTooltipState();
}

class _HoverTooltipState extends State<HoverTooltip> {
  OverlayEntry? _entry;

  void _show(Offset globalPosition) {
    _hide();
    if (widget.message.isEmpty) return;
    _entry = OverlayEntry(
      builder: (_) {
        final screen = MediaQuery.of(context).size;
        const maxW = 300.0;
        var left = globalPosition.dx + 12;
        var top = globalPosition.dy + 12;
        if (left + maxW > screen.width) left = globalPosition.dx - maxW - 12;
        if (top + 80 > screen.height) top = globalPosition.dy - 80;
        return Positioned(
          left: left,
          top: top,
          child: IgnorePointer(
            child: Material(
              elevation: 4,
              borderRadius: BorderRadius.circular(4),
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 300),
                child: Padding(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 4,
                  ),
                  child: Text(
                    widget.message,
                    style: const TextStyle(fontSize: 12),
                  ),
                ),
              ),
            ),
          ),
        );
      },
    );
    Overlay.of(context).insert(_entry!);
  }

  void _hide() {
    _entry?.remove();
    _entry = null;
  }

  @override
  void dispose() {
    _hide();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      hitTestBehavior: HitTestBehavior.translucent,
      onEnter: (e) => _show(e.position),
      onHover: (e) {
        _hide();
        _show(e.position);
      },
      onExit: (_) => _hide(),
      child: widget.child,
    );
  }
}

Path _hexPath(double w, double h) {
  return Path()
    ..moveTo(0, h * 0.5)
    ..lineTo(w * 0.25, 0)
    ..lineTo(w * 0.75, 0)
    ..lineTo(w, h * 0.5)
    ..lineTo(w * 0.75, h)
    ..lineTo(w * 0.25, h)
    ..close();
}

class HexPainter extends CustomPainter {
  HexPainter({
    required this.borderColor,
    required this.fillColor,
    required this.borderWidth,
  });

  final Color borderColor;
  final Color fillColor;
  final double borderWidth;

  @override
  void paint(Canvas canvas, Size size) {
    final outerPath = _hexPath(size.width, size.height);
    canvas.drawPath(outerPath, Paint()..color = borderColor);
    final inset = borderWidth;
    final innerW = size.width - inset * 2;
    final innerH = size.height - inset * 2;
    final innerPath = _hexPath(innerW, innerH);
    canvas.save();
    canvas.translate(inset, inset);
    canvas.drawPath(innerPath, Paint()..color = fillColor);
    canvas.restore();
  }

  @override
  bool shouldRepaint(HexPainter oldDelegate) =>
      borderColor != oldDelegate.borderColor ||
      fillColor != oldDelegate.fillColor ||
      borderWidth != oldDelegate.borderWidth;
}
