import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

void main() {
  runApp(const BlueLabApp());
}

class BlueLabApp extends StatelessWidget {
  const BlueLabApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Blue Lab Calculator',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.light,
        scaffoldBackgroundColor: const Color(0xFFE8F0FE),
        cardColor: const Color(0xFFFFFFFF),
        dividerColor: const Color(0xFFB0C4DE),
        colorScheme: const ColorScheme.light(
          primary: Color(0xFF1A56A8),
          secondary: Color(0xFF3D7AB8),
          surface: Color(0xFFFFFFFF),
          onSurface: Color(0xFF1A2A3A),
        ),
        useMaterial3: true,
      ),
      home: const HomeScreen(),
    );
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  late final Future<ParsedData> _dataFuture = _loadData();
  int _selectedPairIndex = 0;
  final Set<int> _activeCells = <int>{};
  bool _hardCap = true;
  int _moveLevel = 5;
  int _rightTab = 0;
  bool _initialActivationDone = false;

  static const _hexDirections = [
    [1, 0, -1], [-1, 0, 1],
    [0, 1, -1], [0, -1, 1],
    [1, -1, 0], [-1, 1, 0],
  ];

  bool _isAdjacentToCenter(GridCellData cell) {
    for (final d in _hexDirections) {
      if (cell.q == d[0] && cell.r == d[1] && cell.s == d[2]) return true;
    }
    return false;
  }

  bool _isAdjacentToActiveOrCenter(GridCellData cell, List<GridCellData> allCells) {
    for (final d in _hexDirections) {
      final nq = cell.q + d[0];
      final nr = cell.r + d[1];
      final ns = cell.s + d[2];
      if (nq == 0 && nr == 0 && ns == 0) return true;
      for (final other in allCells) {
        if (other.q == nq && other.r == nr && other.s == ns && _activeCells.contains(other.cellNumber)) {
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
    final queue = <List<int>>[[0, 0, 0]];
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
      if (cell.energyCost == 0 && cell.moveLevel <= _moveLevel &&
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

          final selectedEnergy = 60 - selectedPair.cells
              .where((c) => _activeCells.contains(c.cellNumber))
              .fold<int>(0, (sum, c) => sum + c.energyCost);
          final selectedOrbs = selectedPair.cells
              .where((c) => _activeCells.contains(c.cellNumber))
              .fold<int>(0, (sum, c) => sum + c.orbCost);

          return Row(
            children: [
              Expanded(
                flex: 5,
                child: Column(
                  children: [
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
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
                                      final cell = selectedPair.cells.firstWhere((c) => c.cellNumber == cn);
                                      return cell.moveLevel > i;
                                    });
                                    if (_hardCap) _pruneDisconnected(selectedPair.cells);
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
                                      _activateFreeCenterCells(selectedPair.cells);
                                    }
                                  })
                                : null,
                            icon: const Icon(Icons.restart_alt),
                            tooltip: 'Reset Grid',
                          ),
                          const SizedBox(width: 8),
                          const Text('Hard Cap'),
                          Switch(
                            value: _hardCap,
                            onChanged: (value) {
                              setState(() {
                                _hardCap = value;
                                if (value) {
                                  _activateFreeCenterCells(selectedPair.cells);
                                  _pruneDisconnected(selectedPair.cells);
                                }
                              });
                            },
                          ),
                        ],
                      ),
                    ),
                    Expanded(
                      child: Card(
                        margin: const EdgeInsets.all(8),
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
                                if (_hardCap) _pruneDisconnected(selectedPair.cells);
                              } else {
                                final cell = selectedPair.cells.firstWhere((c) => c.cellNumber == cellNumber);
                                if (cell.moveLevel > _moveLevel) return;
                                if (_hardCap && !_isAdjacentToActiveOrCenter(cell, selectedPair.cells)) return;
                                _activeCells.add(cellNumber);
                              }
                            });
                          },
                          onSelectPair: (index) {
                            setState(() {
                              _selectedPairIndex = index;
                              _activeCells.clear();
                              if (_hardCap) {
                                _activateFreeCenterCells(data.pairs[index].cells);
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
                flex: 3,
                child: RightPanel(
                  pair: selectedPair,
                  activeCells: _activeCells,
                  selectedTab: _rightTab,
                  onTabChanged: (tab) => setState(() => _rightTab = tab),
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
  });

  final SyncPairData pair;
  final Set<int> activeCells;
  final int selectedTab;
  final ValueChanged<int> onTabChanged;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            pair.displayName,
            style: Theme.of(context).textTheme.titleLarge,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
          if (pair.releaseDate != null)
            Text(
              'Disponible: ${pair.releaseDate!.day}/${pair.releaseDate!.month}/${pair.releaseDate!.year}',
              style: Theme.of(context).textTheme.bodySmall,
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
                ? SyncPairOverview(pair: pair)
                : DamageCalculatorPlaceholder(pair: pair, activeCells: activeCells),
          ),
        ],
      ),
    );
  }
}

class SyncPairOverview extends StatefulWidget {
  const SyncPairOverview({super.key, required this.pair});

  final SyncPairData pair;

  @override
  State<SyncPairOverview> createState() => _SyncPairOverviewState();
}

class _SyncPairOverviewState extends State<SyncPairOverview> {
  bool _showTera = false;

  SyncPairData get pair => widget.pair;

  static const _typeColors = <String, Color>{
    'normal': Color(0xFFA8A878), 'fire': Color(0xFFF08030), 'water': Color(0xFF6890F0),
    'grass': Color(0xFF78C850), 'electric': Color(0xFFF8D030), 'ice': Color(0xFF98D8D8),
    'fighting': Color(0xFFC03028), 'poison': Color(0xFFA040A0), 'ground': Color(0xFFE0C068),
    'flying': Color(0xFFA890F0), 'psychic': Color(0xFFF85888), 'bug': Color(0xFFA8B820),
    'rock': Color(0xFFB8A038), 'ghost': Color(0xFF705898), 'dragon': Color(0xFF7038F8),
    'dark': Color(0xFF705848), 'steel': Color(0xFFB8B8D0), 'fairy': Color(0xFFEE99AC),
  };

  Widget _teraTab(String label, bool selected) {
    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() => _showTera = label == 'Tera'),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(
            color: selected
                ? (label == 'Tera' ? const Color(0xFF6C5CE7) : Theme.of(context).colorScheme.primary)
                : Colors.transparent,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(
              color: label == 'Tera' ? const Color(0xFF6C5CE7) : Theme.of(context).colorScheme.primary,
              width: 1.5,
            ),
          ),
          alignment: Alignment.center,
          child: Text(
            label,
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w700,
              color: selected ? Colors.white : Theme.of(context).colorScheme.onSurface,
            ),
          ),
        ),
      ),
    );
  }

  Color _typeColor(String type) {
    return _typeColors[type.toLowerCase()] ?? Colors.grey;
  }

  Widget _typeChip(String type) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: _typeColor(type),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(type, style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w600)),
    );
  }

  Widget _moveCard(BuildContext context, MoveData move) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: move.type.isNotEmpty ? _typeColor(move.type).withValues(alpha: 0.12) : Theme.of(context).colorScheme.surface,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: move.type.isNotEmpty ? _typeColor(move.type).withValues(alpha: 0.5) : Colors.grey.shade300),
      ),
      child: Padding(
        padding: const EdgeInsets.all(10),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                if (move.isSync) Padding(
                  padding: const EdgeInsets.only(right: 6),
                  child: Icon(Icons.star, size: 14, color: Colors.purple.shade300),
                ),
                Expanded(child: Text(move.name, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13))),
                if (move.type.isNotEmpty) _typeChip(move.type),
              ],
            ),
            if (move.description.isNotEmpty) Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(move.description, style: TextStyle(fontSize: 11, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7))),
            ),
            if (move.power.isNotEmpty || move.accuracy.isNotEmpty || move.gauge.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 6),
                child: Wrap(
                  spacing: 12,
                  children: [
                    if (move.power.isNotEmpty && move.power != '--') Text('⚔ ${move.power}', style: const TextStyle(fontSize: 11)),
                    if (move.accuracy.isNotEmpty && move.accuracy != '--') Text('🎯 ${move.accuracy}', style: const TextStyle(fontSize: 11)),
                    if (move.gauge.isNotEmpty && move.gauge != '--') Text('⚡ ${move.gauge}', style: const TextStyle(fontSize: 11)),
                    if (move.target.isNotEmpty && move.target != '--') Text('🎯 ${move.target}', style: const TextStyle(fontSize: 11)),
                    if (move.category.isNotEmpty) Text(move.category, style: TextStyle(fontSize: 11, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5))),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _passiveCard(BuildContext context, PassiveData passive) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: Colors.amber.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.amber.withValues(alpha: 0.3)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(10),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(passive.name, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13)),
            if (passive.description.isNotEmpty) Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(passive.description, style: TextStyle(fontSize: 11, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7))),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final displayMoves = _showTera && pair.teraMove != null
        ? [...pair.moves, pair.teraMove!]
        : pair.moves;
    final displayPassives = _showTera
        ? [...pair.passives, ...pair.teraPassives]
        : pair.passives;

    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              if (pair.role.isNotEmpty) Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(color: Colors.blueGrey, borderRadius: BorderRadius.circular(4)),
                child: Text(pair.role, style: const TextStyle(color: Colors.white, fontSize: 12)),
              ),
              const SizedBox(width: 6),
              if (pair.type.isNotEmpty) _typeChip(pair.type),
            ],
          ),
          if (pair.hasTera) Padding(
            padding: const EdgeInsets.only(top: 10),
            child: Row(
              children: [
                _teraTab('Base', !_showTera),
                const SizedBox(width: 6),
                _teraTab('Tera', _showTera),
              ],
            ),
          ),
          if (pair.passives.isNotEmpty) ...[
            const Padding(
              padding: EdgeInsets.only(top: 16, bottom: 8),
              child: Text('Passives', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
            ),
            for (final passive in displayPassives) _passiveCard(context, passive),
          ],
          if (pair.moves.isNotEmpty) ...[
            const Padding(
              padding: EdgeInsets.only(top: 8, bottom: 8),
              child: Text('Moves', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
            ),
            for (final move in displayMoves) _moveCard(context, move),
          ],
        ],
      ),
    );
  }
}

class DamageCalculatorPlaceholder extends StatelessWidget {
  const DamageCalculatorPlaceholder({
    super.key,
    required this.pair,
    required this.activeCells,
  });

  final SyncPairData pair;
  final Set<int> activeCells;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Calculadora de Daño',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          const SizedBox(height: 8),
          const Text('Próximamente:'),
          const Text('- Inputs de stats, buffs y objetivo'),
          const Text('- Cálculo de daño base'),
          const Text('- Impacto de celdas activadas'),
        ],
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
      return const Center(child: Text('Este personaje no tiene grid cargado.'));
    }

    // Inject a virtual center cell at (0,0,0) if none exists.
    final allCells = cells.any((c) => c.q == 0 && c.r == 0 && c.s == 0)
        ? cells
        : [
            const GridCellData(
              cellNumber: -1, q: 0, r: 0, s: 0,
              energyCost: 0, orbCost: 0,
              title: '', description: '', colorKind: '',
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

    return Center(
      child: Scrollbar(
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
            width: contentW,
            height: contentH,
            child: Stack(
              children: [
                for (final cell in allCells)
                  Positioned(
                    left: coords[cell.cellNumber]!.dx - cMinX,
                    top: coords[cell.cellNumber]!.dy - cMinY,
                    child: (cell.q == 0 && cell.r == 0 && cell.s == 0)
                        ? GestureDetector(
                            onTap: () => _showPairPicker(context),
                            child: SizedBox(
                              width: tileW,
                              height: tileH,                              child: Center(
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
                            child: Builder(builder: (_) {
                              final colorKind = _isSyncMoveTile(cell) ? '(sync move)' : cell.colorKind;
                              final (activeC, darkC) = _gridColors(colorKind);
                              return HexTile(
                                radius: tileRadius,
                                activeColor: activeC,
                                darkColor: darkC,
                                active: activeCells.contains(cell.cellNumber),
                                locked: cell.moveLevel > moveLevel,
                                label: _buildCellLabel(cell, syncMoveName: syncMoveName),
                                onTap: () => onToggleCell(cell.cellNumber),
                              );
                            }),
                          ),
                  ),
              ],
            ),
          ),
        ),
          ),
        ),
      ),
    );
  }

  void _showPairPicker(BuildContext context) {
    showDialog(
      context: context,
      builder: (_) => SimpleDialog(
        title: const Text('Seleccionar personaje'),
        children: [
          SizedBox(
            width: 400,
            height: 500,
            child: ListView.builder(
              itemCount: pairs.length,
              itemBuilder: (context, index) {
                final pair = pairs[index];
                return ListTile(
                  title: Text(pair.displayName),
                  subtitle: Text(
                    [
                      if (pair.role.isNotEmpty) pair.role,
                      if (pair.type.isNotEmpty) pair.type,
                    ].join(' | '),
                  ),
                  onTap: () {
                    Navigator.of(context).pop();
                    onSelectPair(index);
                  },
                );
              },
            ),
          ),
        ],
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
    return buffer.toString().trim();
  }

  static String _buildCellLabel(GridCellData cell, {String syncMoveName = ''}) {
    final title = cell.title.trim();
    if (title.isEmpty) {
      return '${cell.cellNumber}';
    }
    if (syncMoveName.isNotEmpty && title.startsWith(syncMoveName)) {
      final rest = title.substring(syncMoveName.length).trim();
      final match = RegExp(r':\s*Power\s+(\d+)', caseSensitive: false).firstMatch(rest);
      if (match != null) return 'Sync Move Power +${match.group(1)}';
    }
    return title.replaceAllMapped(
      RegExp(r'Move Gauge Refresh\s+(\d+)', caseSensitive: false),
      (match) => 'MGR${match.group(1)}',
    ).replaceAllMapped(
      RegExp(r'MP Refresh\s+(\d+)', caseSensitive: false),
      (match) => 'MPR${match.group(1)}',
    );
  }

  static const _tileColors = <String, (Color active, Color dark)>{
    'stat':        (Color(0xFF4A90D9), Color(0xFF18529C)),
    'move boost':  (Color(0xFF2ECC71), Color(0xFF056E50)),
    'move effect': (Color(0xFFE74C3C), Color(0xFFA7364A)),
    'sync':        (Color(0xFF9B59B6), Color(0xFF432D7F)),
    'passive':     (Color(0xFFF1C40F), Color(0xFF907500)),
  };

  static (Color, Color) _gridColors(String kind) {
    final n = kind.toLowerCase();
    if (n.contains('(sync move)'))   return _tileColors['sync']!;
    if (n.contains('(stat)'))        return _tileColors['stat']!;
    if (n.contains('(move boost)'))  return _tileColors['move boost']!;
    if (n.contains('(move effect)')) return _tileColors['move effect']!;
    if (n.contains('(passive)'))     return _tileColors['passive']!;
    return _tileColors['passive']!;
  }

  bool _isSyncMoveTile(GridCellData cell) {
    if (syncMoveName.isEmpty) return false;
    return cell.title.startsWith(syncMoveName);
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
        painter: HexPainter(borderColor: borderColor, fillColor: fillColor, borderWidth: 5.0),
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
                        Shadow(offset: Offset(1, 1), blurRadius: 2, color: Colors.black),
                        Shadow(offset: Offset(-1, -1), blurRadius: 2, color: Colors.black),
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
          style: TextStyle(
            fontWeight: FontWeight.w700,
            fontSize: size,
          ),
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
      builder: (_) => Positioned(
        left: globalPosition.dx + 12,
        top: globalPosition.dy + 12,
        child: IgnorePointer(
          child: Material(
            elevation: 4,
            borderRadius: BorderRadius.circular(4),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              child: Text(widget.message, style: const TextStyle(fontSize: 12)),
            ),
          ),
        ),
      ),
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
  HexPainter({required this.borderColor, required this.fillColor, required this.borderWidth});

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

class ParsedData {
  const ParsedData({required this.pairs});

  final List<SyncPairData> pairs;
}

class SyncPairData {
  const SyncPairData({
    required this.number,
    required this.displayName,
    required this.role,
    required this.type,
    required this.rarity,
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
  });

  final int number;
  final String displayName;
  final String role;
  final String type;
  final String weakness;
  final String rarity;
  final List<GridCellData> cells;
  final DateTime? releaseDate;
  final String syncMoveName;
  final List<MoveData> moves;
  final List<PassiveData> passives;
  final String description;
  final bool hasTera;
  final MoveData? teraMove;
  final List<PassiveData> teraPassives;
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
}

Future<ParsedData> _loadData() async {
  final kitsText = await rootBundle.loadString('docs/kits.txt');
  final gridsText = await rootBundle.loadString('docs/grids.txt');

  final kitMap = _parseKits(kitsText);
  final gridMap = _parseGrids(gridsText);

  final allNumbers = <int>{...kitMap.keys, ...gridMap.keys}.toList()..sort();
  final pairs = allNumbers
      .where((number) => (gridMap[number] ?? []).isNotEmpty)
      .map((number) {
    final kit = kitMap[number];
    final cells = gridMap[number]!;
    return SyncPairData(
      number: number,
      displayName: kit?.displayName ?? 'No. $number',
      role: kit?.role ?? '',
      type: kit?.type ?? '',
      weakness: kit?.weakness ?? '',
      rarity: kit?.rarity ?? '',
      cells: cells,
      releaseDate: kit?.releaseDate,
      syncMoveName: kit?.syncMoveName ?? '',
      moves: kit?.moves ?? [],
      passives: kit?.passives ?? [],
      description: kit?.description ?? '',
      hasTera: kit?.hasTera ?? false,
      teraMove: kit?.teraMove,
      teraPassives: kit?.teraPassives ?? [],
    );
  }).toList()
    ..sort((a, b) {
      final da = a.releaseDate ?? DateTime(2000);
      final db = b.releaseDate ?? DateTime(2000);
      return db.compareTo(da);
    });

  return ParsedData(pairs: pairs);
}

Map<int, _KitInfo> _parseKits(String input) {
  final result = <int, _KitInfo>{};
  final sections = _splitByNoBlocks(input);
  final numberRegex = RegExp(r'^No\. (\d+)\s+(.*)$');

  for (final section in sections) {
    final lines = section
        .split('\n')
        .map((line) => line.trimRight())
        .where((line) => line.isNotEmpty)
        .toList();
    if (lines.isEmpty) continue;

    final headerMatch = numberRegex.firstMatch(lines.first.trim());
    if (headerMatch == null) continue;

    final number = int.parse(headerMatch.group(1)!);
    final displayName = headerMatch.group(2)!.trim();
    String role = '';
    String type = '';
    String weakness = '';
    String rarity = '';
    String syncMoveName = '';
    String description = '';
    DateTime? releaseDate;
    final moves = <MoveData>[];
    final passives = <PassiveData>[];

    for (int i = 1; i < lines.length; i++) {
      final line = lines[i];
      if (line.contains('Tera Details')) break;
      if (line.startsWith('Role:')) {
        role = line.replaceFirst('Role:', '').split('|').first.trim();
      } else if (line.startsWith('Type:')) {
        final parts = line.replaceFirst('Type:', '').split('|');
        type = parts.first.trim();
        if (parts.length > 1) {
          weakness = parts[1].replaceAll(RegExp(r'Weakness:\s*'), '').trim();
        }
      } else if (line.startsWith('Rarity:')) {
        rarity = line.replaceFirst('Rarity:', '').trim();
      } else if (line.startsWith('Descriptions:')) {
        description = line.replaceFirst('Descriptions:', '').trim();
      } else if (line.startsWith('Sync Move:')) {
        syncMoveName = line.replaceFirst('Sync Move:', '').trim();
      } else if (line.startsWith('Sync Pair Available:')) {
        final dateStr = line.replaceFirst('Sync Pair Available:', '').trim();
        final match = RegExp(r'(\d+)/(\d+)/(\d+)').firstMatch(dateStr);
        if (match != null) {
          releaseDate = DateTime(
            int.parse(match.group(3)!),
            int.parse(match.group(2)!),
            int.parse(match.group(1)!),
          );
        }
      } else if (RegExp(r'^Move \d+:').hasMatch(line)) {
        final moveName = line.replaceFirst(RegExp(r'^Move \d+:\s*'), '').trim();
        String mType = '', mCat = '', mPower = '', mAcc = '', mGauge = '', mTarget = '', mDesc = '';
        for (int j = i + 1; j < lines.length && !lines[j].startsWith('Move ') && !lines[j].startsWith('Sync Move:') && !lines[j].startsWith('Passive '); j++) {
          final ml = lines[j];
          if (ml.startsWith('Type:')) mType = ml.replaceFirst('Type:', '').trim();
          else if (ml.startsWith('Category:')) mCat = ml.replaceFirst('Category:', '').trim();
          else if (ml.startsWith('Description:')) mDesc = ml.replaceFirst('Description:', '').trim();
          else if (ml.startsWith('Power:')) {
            final attrs = ml.split('|').map((e) => e.trim()).toList();
            for (final a in attrs) {
              if (a.startsWith('Power:')) mPower = a.replaceFirst('Power:', '').trim();
              else if (a.startsWith('Accuracy:')) mAcc = a.replaceFirst('Accuracy:', '').trim();
              else if (a.startsWith('Gauge:')) mGauge = a.replaceFirst('Gauge:', '').trim();
              else if (a.startsWith('Target:')) mTarget = a.replaceFirst('Target:', '').trim();
            }
          }
        }
        moves.add(MoveData(name: moveName, type: mType, category: mCat, power: mPower, accuracy: mAcc, gauge: mGauge, target: mTarget, description: mDesc));
      } else if (RegExp(r'^Passive \d+:').hasMatch(line)) {
        final passiveName = line.replaceFirst(RegExp(r'^Passive \d+:\s*'), '').trim();
        String pDesc = '';
        if (i + 1 < lines.length) {
          final pl = lines[i + 1].trim();
          if (pl.isNotEmpty && !pl.startsWith('Passive ') && !RegExp(r'^[A-Z].*:').hasMatch(pl)) {
            pDesc = pl;
          }
        }
        passives.add(PassiveData(name: passiveName, description: pDesc));
      }
    }

    if (syncMoveName.isNotEmpty) {
      String smType = '', smCat = '', smPower = '', smDesc = '';
      bool inSync = false;
      for (final line in lines) {
        if (line.startsWith('Sync Move:')) { inSync = true; continue; }
        if (inSync) {
          if (line.startsWith('Type:')) smType = line.replaceFirst('Type:', '').trim();
          else if (line.startsWith('Category:')) smCat = line.replaceFirst('Category:', '').trim();
          else if (line.startsWith('Description:')) smDesc = line.replaceFirst('Description:', '').trim();
          else if (line.startsWith('Power:')) {
            smPower = line.split('|').first.replaceFirst('Power:', '').trim();
            inSync = false;
          }
        }
      }
      moves.add(MoveData(name: syncMoveName, type: smType, category: smCat, power: smPower, description: smDesc, isSync: true));
    }

    MoveData? teraMove;
    final teraPassives = <PassiveData>[];
    bool inTera = false;
    for (int i = 1; i < lines.length; i++) {
      final line = lines[i];
      if (line.contains('Tera Details')) { inTera = true; continue; }
      if (inTera && line.startsWith('----')) break;
      if (inTera && line.contains('Tera Move:')) {
        final tmName = line.replaceFirst(RegExp(r'.*Tera Move:\s*'), '').trim();
        String tmType = '', tmCat = '', tmPower = '', tmAcc = '', tmGauge = '', tmTarget = '', tmDesc = '';
        for (int j = i + 1; j < lines.length; j++) {
          final ml = lines[j];
          if (ml.contains('Passives Details') || ml.startsWith('----')) break;
          if (ml.startsWith('Type:')) tmType = ml.replaceFirst('Type:', '').trim();
          else if (ml.startsWith('Category:')) tmCat = ml.replaceFirst('Category:', '').trim();
          else if (ml.startsWith('Description:')) tmDesc = ml.replaceFirst('Description:', '').trim();
          else if (ml.startsWith('Power:')) {
            final attrs = ml.split('|').map((e) => e.trim()).toList();
            for (final a in attrs) {
              if (a.startsWith('Power:')) tmPower = a.replaceFirst('Power:', '').trim();
              else if (a.startsWith('Accuracy:')) tmAcc = a.replaceFirst('Accuracy:', '').trim();
              else if (a.startsWith('Gauge:')) tmGauge = a.replaceFirst('Gauge:', '').trim();
              else if (a.startsWith('Target:')) tmTarget = a.replaceFirst('Target:', '').trim();
            }
          }
        }
        teraMove = MoveData(name: tmName, type: tmType, category: tmCat, power: tmPower, accuracy: tmAcc, gauge: tmGauge, target: tmTarget, description: tmDesc);
      }
      if (inTera && RegExp(r'^Passive \d+:').hasMatch(line)) {
        final pName = line.replaceFirst(RegExp(r'^Passive \d+:\s*'), '').trim();
        String pDesc = '';
        if (i + 1 < lines.length) {
          final pl = lines[i + 1].trim();
          if (pl.isNotEmpty && !pl.startsWith('Passive ') && !pl.startsWith('-') && !pl.startsWith('----')) {
            pDesc = pl;
          }
        }
        teraPassives.add(PassiveData(name: pName, description: pDesc));
      }
    }

    result[number] = _KitInfo(
      displayName: displayName,
      role: role,
      type: type,
      weakness: weakness,
      rarity: rarity,
      releaseDate: releaseDate,
      syncMoveName: syncMoveName,
      moves: moves,
      passives: passives,
      description: description,
      hasTera: teraMove != null,
      teraMove: teraMove,
      teraPassives: teraPassives,
    );
  }

  return result;
}

Map<int, List<GridCellData>> _parseGrids(String input) {
  final result = <int, List<GridCellData>>{};
  final sections = _splitByNoBlocks(input);
  final numberRegex = RegExp(r'^No\. (\d+)\s+(.*)$');

  for (final section in sections) {
    final lines = section.split('\n').map((line) => line.trimRight()).toList();
    if (lines.isEmpty) continue;

    final headerLine = lines.firstWhere(
      (line) => line.trim().startsWith('No.'),
      orElse: () => '',
    );
    if (headerLine.isEmpty) continue;

    final headerMatch = numberRegex.firstMatch(headerLine.trim());
    if (headerMatch == null) continue;
    final number = int.parse(headerMatch.group(1)!);
    result[number] = _parseCellsFromGridSection(lines);
  }

  return result;
}

List<GridCellData> _parseCellsFromGridSection(List<String> lines) {
  final cells = <GridCellData>[];
  final cellHeaderRegex = RegExp(
    r'^Cell\s+(\d+)\s+\|\s+🎯\s+Cord\s+\((-?\d+),(-?\d+),(-?\d+)\)\s+\|\s+Cost:\s+⚡\s+(\d+)\s+Energy\s+\|\s+🔮\s+(\d+)\s+Sync Orb\(s\)',
  );

  int index = 0;
  while (index < lines.length) {
    final line = lines[index].trim();
    final headerMatch = cellHeaderRegex.firstMatch(line);
    if (headerMatch == null) {
      index++;
      continue;
    }

    final cellNumber = int.parse(headerMatch.group(1)!);
    final q = int.parse(headerMatch.group(2)!);
    final r = int.parse(headerMatch.group(3)!);
    final s = int.parse(headerMatch.group(4)!);
    final energy = int.parse(headerMatch.group(5)!);
    final orbs = int.parse(headerMatch.group(6)!);

    final details = <String>[];
    index++;
    while (index < lines.length && !lines[index].trim().startsWith('Cell ')) {
      final current = lines[index].trim();
      if (current.isNotEmpty) {
        details.add(current);
      }
      if (current.startsWith('================================END')) {
        break;
      }
      index++;
    }

    final isExpansion = details.any((line) => line.startsWith('Grid Expand Unlock:'));
    if (isExpansion) {
      index++;
      continue;
    }

    final filtered = details
        .where(
          (line) =>
              !line.startsWith('Requirements:') &&
              !line.startsWith('Grid Expand Unlock:') &&
              !line.startsWith('Color Grid:') &&
              !line.startsWith('Move:'),
        )
        .toList();
    final colorLine = details.firstWhere(
      (line) => line.startsWith('Color Grid:'),
      orElse: () => '',
    );
    final reqLine = details.firstWhere(
      (line) => line.contains('Move level must be'),
      orElse: () => '',
    );
    final moveLevelMatch = RegExp(r'Move level must be (\d+)').firstMatch(reqLine);
    final moveLevel = moveLevelMatch != null ? int.parse(moveLevelMatch.group(1)!) : 1;

    final title = filtered.isNotEmpty ? filtered.first : '';
    final description = filtered.length > 1 ? filtered[1] : '';
    final colorKind = colorLine.isNotEmpty
        ? colorLine.replaceFirst('Color Grid:', '').trim()
        : 'Unknown';

    cells.add(
      GridCellData(
        cellNumber: cellNumber,
        q: q,
        r: r,
        s: s,
        energyCost: energy,
        orbCost: orbs,
        title: title,
        description: description,
        colorKind: colorKind,
        moveLevel: moveLevel,
      ),
    );
  }

  return cells;
}

List<String> _splitByNoBlocks(String raw) {
  final lines = raw.split('\n');
  final sections = <String>[];
  final current = <String>[];

  for (final line in lines) {
    final trimmed = line.trim();
    if (trimmed.startsWith('No. ') && current.isNotEmpty) {
      sections.add(current.join('\n'));
      current.clear();
    }
    if (trimmed.startsWith('No. ') || current.isNotEmpty) {
      current.add(line);
    }
  }

  if (current.isNotEmpty) {
    sections.add(current.join('\n'));
  }

  return sections;
}

class _KitInfo {
  const _KitInfo({
    required this.displayName,
    required this.role,
    required this.type,
    this.weakness = '',
    required this.rarity,
    this.releaseDate,
    this.syncMoveName = '',
    this.moves = const [],
    this.passives = const [],
    this.description = '',
    this.hasTera = false,
    this.teraMove,
    this.teraPassives = const [],
  });

  final String displayName;
  final String role;
  final String type;
  final String weakness;
  final String rarity;
  final DateTime? releaseDate;
  final String syncMoveName;
  final List<MoveData> moves;
  final List<PassiveData> passives;
  final String description;
  final bool hasTera;
  final MoveData? teraMove;
  final List<PassiveData> teraPassives;
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
}

class PassiveData {
  const PassiveData({required this.name, required this.description});

  final String name;
  final String description;
}
