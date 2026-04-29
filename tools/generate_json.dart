import 'dart:convert';
import 'dart:io';

void main() {
  final docsDir = Directory('docs');
  final kitFiles = <String>[];
  final gridFiles = <String>[];
  for (final f in docsDir.listSync().whereType<File>()) {
    final name = f.path.split(RegExp(r'[\\/]')).last.toLowerCase();
    if (name.contains('sync pair information') || name == 'kits.txt') {
      kitFiles.add(f.readAsStringSync());
    } else if (name.contains('sync grid') ||
        name.contains('all new sync grid') ||
        name == 'grids.txt') {
      gridFiles.add(f.readAsStringSync());
    }
  }

  final kitMap = parseKits(kitFiles.join('\n'));
  final gridMap = parseGrids(gridFiles.join('\n'));

  final allNumbers = <int>{...kitMap.keys, ...gridMap.keys}.toList()..sort();
  final pairs = <Map<String, dynamic>>[];

  for (final number in allNumbers) {
    final grid = gridMap[number];
    if (grid == null || grid.isEmpty) continue;
    final kit = kitMap[number];
    if (kit == null) continue;
    pairs.add({
      'number': number,
      'displayName': kit['displayName'] ?? 'No. $number',
      'role': kit['role'] ?? '',
      'exRole': kit['exRole'] ?? '',
      'type': kit['type'] ?? '',
      'weakness': kit['weakness'] ?? '',
      'rarity': kit['rarity'] ?? 5,
      'hasEx': kit['hasEx'] ?? false,
      'hasSuperAwakening': kit['hasSuperAwakening'] ?? false,
      'syncMoveName': kit['syncMoveName'] ?? '',
      'releaseDate': kit['releaseDate'],
      'moves': kit['moves'] ?? [],
      'passives': kit['passives'] ?? [],
      'hasTera': kit['hasTera'] ?? false,
      'teraMove': kit['teraMove'],
      'teraPassives': kit['teraPassives'] ?? [],
      'stats': kit['stats'] ?? {},
      'teraStatMultiplier': _buildTeraStatMultiplier(kit['teraPassives'] ?? []),
      'megaStatMultiplier': kit['megaStatMultiplier'] ?? {},
      'megaStats': kit['megaStats'] ?? {},
      'variations': kit['variations'] ?? [],
      'cells': grid,
    });
  }

  final json = const JsonEncoder.withIndent('  ').convert(pairs);
  File('assets/data/sync_pairs.json').writeAsStringSync(json);
  print('Generated assets/data/sync_pairs.json with ${pairs.length} pairs');
}

final _passiveHeaderRegex = RegExp(r'^Passive \d+(?:\([^)]*\))?:');

Map<int, Map<String, dynamic>> parseKits(String input) {
  final result = <int, Map<String, dynamic>>{};
  final sections = splitByNoBlocks(input);
  final numberRegex = RegExp(r'^No\. (\d+)\s+(.*)$');

  for (final section in sections) {
    final lines = section
        .split('\n')
        .map((l) => l.trimRight())
        .where((l) => l.isNotEmpty)
        .toList();
    if (lines.isEmpty) continue;
    final headerMatch = numberRegex.firstMatch(lines.first.trim());
    if (headerMatch == null) continue;

    final number = int.parse(headerMatch.group(1)!);
    final displayName = headerMatch.group(2)!.trim();
    String role = '', type = '', weakness = '', syncMoveName = '', exRole = '';
    int rarity = 5;
    bool hasEx = false;
    String? releaseDate;
    final moves = <Map<String, dynamic>>[];
    final passives = <Map<String, dynamic>>[];

    Map<String, dynamic>? superAwakenedPassive;

    for (int i = 1; i < lines.length; i++) {
      final line = lines[i];
      if (line.contains('Tera Details') || line.contains('Variation Details'))
        break;
      if (line.contains('Superawakened Passive:')) {
        final saName = line.replaceFirst(RegExp(r'.*Superawakened Passive:\s*'), '').trim();
        String saDesc = '';
        if (i + 1 < lines.length) {
          final pl = lines[i + 1].trim();
          if (pl.isNotEmpty &&
              !pl.startsWith('Passive ') &&
              !RegExp(r'^(Role|Type|Category|Power|Accuracy|Gauge|Target|Rarity|Method|Sync Pair|EX |Lv\.|HP ):').hasMatch(pl))
            saDesc = pl;
        }
        superAwakenedPassive = {'name': saName, 'description': saDesc, 'locked': true};
        continue;
      }
      if (line.startsWith('Role:')) {
        role = line.replaceFirst('Role:', '').split('|').first.trim();
        final exMatch = RegExp(r'EX Role[^:]*:\s*(\w+)').firstMatch(line);
        if (exMatch != null) exRole = exMatch.group(1)!.trim();
      } else if (line.startsWith('Type:')) {
        final parts = line.replaceFirst('Type:', '').split('|');
        type = parts.first.trim();
        if (parts.length > 1)
          weakness = parts[1].replaceAll(RegExp(r'Weakness:\s*'), '').trim();
      } else if (line.startsWith('Sync Move:')) {
        syncMoveName = line.replaceFirst('Sync Move:', '').trim();
      } else if (line.startsWith('Sync Pair Available:')) {
        final m = RegExp(r'(\d+)/(\d+)/(\d+)').firstMatch(line);
        if (m != null)
          releaseDate =
              '${m.group(3)}-${m.group(2)!.padLeft(2, '0')}-${m.group(1)!.padLeft(2, '0')}';
      } else if (line.startsWith('Rarity:')) {
        rarity = '⭐'.allMatches(line).length;
        if (rarity == 0) rarity = RegExp(r'[★⭐]').allMatches(line).length;
        if (rarity == 0) rarity = 5;
      } else if (line.contains('EX Color')) {
        hasEx = line.contains('Yes');
      } else if (line.contains('EX Effect Available') || line.contains('EX Role Available') || line.toLowerCase().contains('ex available')) {
        hasEx = true;
      } else if (RegExp(r'^Move \d+:').hasMatch(line)) {
        final moveName = line.replaceFirst(RegExp(r'^Move \d+:\s*'), '').trim();
        String mType = '',
            mCat = '',
            mPower = '',
            mAcc = '',
            mGauge = '',
            mTarget = '',
            mDesc = '';
        for (
          int j = i + 1;
          j < lines.length &&
              !lines[j].startsWith('Move ') &&
              !lines[j].startsWith('Sync Move:') &&
              !_passiveHeaderRegex.hasMatch(lines[j]);
          j++
        ) {
          final ml = lines[j];
          if (ml.startsWith('Type:')) {
            mType = ml.replaceFirst('Type:', '').trim();
          } else if (ml.startsWith('Category:'))
            mCat = ml.replaceFirst('Category:', '').trim();
          else if (ml.startsWith('Description:'))
            mDesc = ml.replaceFirst('Description:', '').trim();
          else if (ml.startsWith('Power:')) {
            for (final a in ml.split('|').map((e) => e.trim())) {
              if (a.startsWith('Power:')) {
                mPower = a.replaceFirst('Power:', '').trim();
              } else if (a.startsWith('Accuracy:'))
                mAcc = a.replaceFirst('Accuracy:', '').trim();
              else if (a.startsWith('Gauge:'))
                mGauge = a.replaceFirst('Gauge:', '').trim();
              else if (a.startsWith('Target:'))
                mTarget = a.replaceFirst('Target:', '').trim();
            }
          }
        }
        moves.add({
          'name': moveName,
          'type': mType,
          'category': mCat,
          'power': mPower,
          'accuracy': mAcc,
          'gauge': mGauge,
          'target': mTarget,
          'description': mDesc,
          'isSync': false,
        });
      } else if (_passiveHeaderRegex.hasMatch(line)) {
        final pName = line
            .replaceFirst(RegExp(r'^Passive \d+(?:\([^)]*\))?:\s*'), '')
            .trim();
        String pDesc = '';
        if (i + 1 < lines.length) {
          final pl = lines[i + 1].trim();
          if (pl.isNotEmpty &&
              !pl.startsWith('Passive ') &&
              !RegExp(
                r'^(Role|Type|Category|Power|Accuracy|Gauge|Target|Rarity|Method|Sync Pair|EX |Lv\.|HP ):',
              ).hasMatch(pl))
            pDesc = pl;
        }
        final hasMarker = RegExp(r'Passive \d+\([^)]+\):').hasMatch(line);
        passives.add({'name': pName, 'description': pDesc, 'locked': hasMarker});
      }
    }

    if (syncMoveName.isNotEmpty) {
      String smType = '', smCat = '', smPower = '', smDesc = '';
      bool inSync = false;
      for (final line in lines) {
        if (line.contains('Tera Details') || line.contains('Variation Details'))
          break;
        if (line.startsWith('Sync Move:')) {
          inSync = true;
          continue;
        }
        if (inSync) {
          if (line.startsWith('Type:')) {
            smType = line.replaceFirst('Type:', '').trim();
          } else if (line.startsWith('Category:'))
            smCat = line.replaceFirst('Category:', '').trim();
          else if (line.startsWith('Description:'))
            smDesc = line.replaceFirst('Description:', '').trim();
          else if (line.startsWith('Power:')) {
            smPower = line.split('|').first.replaceFirst('Power:', '').trim();
            inSync = false;
          }
        }
      }
      moves.add({
        'name': syncMoveName,
        'type': smType,
        'category': smCat,
        'power': smPower,
        'description': smDesc,
        'isSync': true,
      });
    }

    Map<String, dynamic>? teraMove;
    final teraPassives = <Map<String, dynamic>>[];
    bool inTera = false;
    for (int i = 1; i < lines.length; i++) {
      final line = lines[i];
      if (line.contains('Tera Details')) {
        inTera = true;
        continue;
      }
      if (inTera && line.startsWith('----')) break;
      if (inTera && line.contains('Tera Move:')) {
        final tmName = line.replaceFirst(RegExp(r'.*Tera Move:\s*'), '').trim();
        String tmType = '',
            tmCat = '',
            tmPower = '',
            tmAcc = '',
            tmGauge = '',
            tmTarget = '',
            tmDesc = '';
        for (int j = i + 1; j < lines.length; j++) {
          final ml = lines[j];
          if (ml.contains('Passives Details') || ml.startsWith('----')) break;
          if (ml.startsWith('Type:')) {
            tmType = ml.replaceFirst('Type:', '').trim();
          } else if (ml.startsWith('Category:'))
            tmCat = ml.replaceFirst('Category:', '').trim();
          else if (ml.startsWith('Description:'))
            tmDesc = ml.replaceFirst('Description:', '').trim();
          else if (ml.startsWith('Power:')) {
            for (final a in ml.split('|').map((e) => e.trim())) {
              if (a.startsWith('Power:')) {
                tmPower = a.replaceFirst('Power:', '').trim();
              } else if (a.startsWith('Accuracy:'))
                tmAcc = a.replaceFirst('Accuracy:', '').trim();
              else if (a.startsWith('Gauge:'))
                tmGauge = a.replaceFirst('Gauge:', '').trim();
              else if (a.startsWith('Target:'))
                tmTarget = a.replaceFirst('Target:', '').trim();
            }
          }
        }
        teraMove = {
          'name': tmName,
          'type': tmType,
          'category': tmCat,
          'power': tmPower,
          'accuracy': tmAcc,
          'gauge': tmGauge,
          'target': tmTarget,
          'description': tmDesc,
        };
      }
      if (inTera && _passiveHeaderRegex.hasMatch(line)) {
        final pName = line
            .replaceFirst(RegExp(r'^Passive \d+(?:\([^)]*\))?:\s*'), '')
            .trim();
        String pDesc = '';
        if (i + 1 < lines.length) {
          final pl = lines[i + 1].trim();
          if (pl.isNotEmpty &&
              !pl.startsWith('Passive ') &&
              !pl.startsWith('-'))
            pDesc = pl;
        }
        teraPassives.add({'name': pName, 'description': pDesc});
      }
    }

    // Parse base stats by level
    final stats = <String, Map<String, int>>{};
    final megaStats = <String, Map<String, int>>{};
    final lvRegex = RegExp(r'^Lv\.\s*(\d+)');
    final statLineRegex = RegExp(
      r'HP\s*:\s*(\d+)\s*\|\s*Attack\s*:\s*(\d+)\s*\|\s*Defense\s*:\s*(\d+)\s*\|\s*Sp\.\s*Atk\s*:\s*(\d+)\s*\|\s*Sp\.\s*Def\s*:\s*(\d+)\s*\|\s*Speed\s*:\s*(\d+)',
    );
    var inMegaStats = false;
    for (int i = 1; i < lines.length; i++) {
      if (lines[i].contains('Mega Stats')) {
        inMegaStats = true;
        continue;
      }
      if (inMegaStats && lines[i].startsWith('----')) {
        inMegaStats = false;
      }
      final lvMatch = lvRegex.firstMatch(lines[i]);
      if (lvMatch != null) {
        final level = lvMatch.group(1)!;
        for (int j = i + 1; j < lines.length && j <= i + 3; j++) {
          final sm = statLineRegex.firstMatch(lines[j]);
          if (sm != null) {
            final target = inMegaStats ? megaStats : stats;
            target[level] = {
              'hp': int.parse(sm.group(1)!),
              'atk': int.parse(sm.group(2)!),
              'def': int.parse(sm.group(3)!),
              'spa': int.parse(sm.group(4)!),
              'spd': int.parse(sm.group(5)!),
              'spe': int.parse(sm.group(6)!),
            };
            break;
          }
        }
      }
    }

    final megaStatMultiplier = <String, double>{};
    final base200 = stats['200'];
    final mega200 = megaStats['200'];
    if (base200 != null && mega200 != null) {
      for (final stat in ['atk', 'def', 'spa', 'spd', 'spe']) {
        final baseValue = base200[stat] ?? 0;
        final megaValue = mega200[stat] ?? 0;
        if (baseValue > 0 && megaValue > 0 && megaValue != baseValue) {
          final roundedValue = double.parse(
            (megaValue / baseValue).toStringAsFixed(2),
          );
          megaStatMultiplier[stat] = roundedValue;
        }
      }
    }

    // If exRole was found, the pair always has EX
    if (exRole.isNotEmpty) hasEx = true;

    // Insert superawakened passive at index 0 if present
    if (superAwakenedPassive != null) {
      passives.insert(0, superAwakenedPassive);
    }

    result[number] = {
      'displayName': displayName,
      'role': role,
      'exRole': exRole,
      'type': type,
      'weakness': weakness,
      'rarity': rarity,
      'hasEx': hasEx,
      'hasSuperAwakening': superAwakenedPassive != null,
      'syncMoveName': syncMoveName,
      'releaseDate': releaseDate,
      'moves': moves,
      'passives': passives,
      'hasTera': teraMove != null,
      'teraMove': teraMove,
      'teraPassives': teraPassives,
      'stats': stats,
      'megaStats': megaStats,
      'megaStatMultiplier': megaStatMultiplier,
      'variations': _parseVariations(lines),
    };
  }
  return result;
}

Map<int, List<Map<String, dynamic>>> parseGrids(String input) {
  final result = <int, List<Map<String, dynamic>>>{};
  final sections = splitByNoBlocks(input);
  final numberRegex = RegExp(r'^No\. (\d+)\s+(.*)$');
  for (final section in sections) {
    final lines = section.split('\n').map((l) => l.trimRight()).toList();
    if (lines.isEmpty) continue;
    final headerLine = lines.firstWhere(
      (l) => l.trim().startsWith('No.'),
      orElse: () => '',
    );
    if (headerLine.isEmpty) continue;
    final m = numberRegex.firstMatch(headerLine.trim());
    if (m == null) continue;
    final number = int.parse(m.group(1)!);
    final cells = parseCells(lines);
    if (result.containsKey(number)) {
      final existing = result[number]!;
      final existingNumbers = existing
          .map((c) => c['cellNumber'] as int)
          .toSet();
      for (final cell in cells) {
        if (!existingNumbers.contains(cell['cellNumber'])) {
          existing.add(cell);
        }
      }
    } else {
      result[number] = cells;
    }
  }
  return result;
}

List<Map<String, dynamic>> parseCells(List<String> lines) {
  final cells = <Map<String, dynamic>>[];
  final re = RegExp(
    r'^Cell\s+(\d+)\s+\|\s+🎯\s+Cord\s+\((-?\d+),(-?\d+),(-?\d+)\)\s+\|\s+Cost:\s+⚡\s+(\d+)\s+Energy\s+\|\s+🔮\s+(\d+)\s+Sync Orb\(s\)',
  );
  int index = 0;
  while (index < lines.length) {
    final m = re.firstMatch(lines[index].trim());
    if (m == null) {
      index++;
      continue;
    }
    final details = <String>[];
    index++;
    while (index < lines.length && !lines[index].trim().startsWith('Cell ')) {
      final c = lines[index].trim();
      if (c.isNotEmpty) details.add(c);
      if (c.startsWith('================================END')) break;
      index++;
    }
    if (details.any((l) => l.startsWith('Grid Expand Unlock:'))) {
      // Include expand cells - they are valid
    }
    final filtered = details
        .where(
          (l) =>
              !l.startsWith('Requirements:') &&
              !l.startsWith('Grid Expand Unlock:') &&
              !l.startsWith('Color Grid:') &&
              !l.startsWith('Move:'),
        )
        .toList();
    final colorLine = details.firstWhere(
      (l) => l.startsWith('Color Grid:'),
      orElse: () => '',
    );
    final reqLine = details.firstWhere(
      (l) => l.contains('Move level must be'),
      orElse: () => '',
    );
    final mlMatch = RegExp(r'Move level must be (\d+)').firstMatch(reqLine);
    cells.add({
      'cellNumber': int.parse(m.group(1)!),
      'q': int.parse(m.group(2)!),
      'r': int.parse(m.group(3)!),
      's': int.parse(m.group(4)!),
      'energyCost': int.parse(m.group(5)!),
      'orbCost': int.parse(m.group(6)!),
      'title': filtered.isNotEmpty ? filtered.first : '',
      'description': filtered.length > 1 ? filtered[1] : '',
      'colorKind': colorLine.isNotEmpty
          ? colorLine.replaceFirst('Color Grid:', '').trim()
          : 'Unknown',
      'moveLevel': mlMatch != null ? int.parse(mlMatch.group(1)!) : 1,
    });
  }
  return cells;
}

Map<String, double> _buildTeraStatMultiplier(List<dynamic> teraPassives) {
  final result = <String, double>{};
  for (final p in teraPassives) {
    final name = (p['name'] ?? '') as String;
    final match = RegExp(
      r'While S-Tera:\s*(\d)\s*Stats.*?(\d+)$',
    ).firstMatch(name);
    if (match != null) {
      final count = int.parse(match.group(1)!);
      final value = int.parse(match.group(2)!);
      final mult = 1.0 + value * 0.1;
      if (count == 5) {
        for (final s in ['atk', 'def', 'spa', 'spd', 'spe']) {
          result[s] = mult;
        }
      }
    }
  }
  return result;
}

List<Map<String, dynamic>> _parseVariations(List<String> lines) {
  final variations = <Map<String, dynamic>>[];
  bool inVariation = false;
  String formName = '';
  final moves = <Map<String, dynamic>>[];
  final passives = <Map<String, dynamic>>[];

  for (int i = 0; i < lines.length; i++) {
    final line = lines[i];
    if (line.contains('Variation Details')) {
      inVariation = true;
      moves.clear();
      passives.clear();
      // Check for form name on next lines
      for (int j = i + 1; j < lines.length && j <= i + 3; j++) {
        final fl = lines[j].trim();
        if (fl.contains('Form:')) {
          formName = fl.replaceFirst(RegExp(r'.*Form:\s*'), '').trim();
          break;
        }
      }
      if (formName.isEmpty) formName = 'Variation';
      continue;
    }
    if (inVariation &&
        (line.contains('Tera Details') || line.startsWith('----'))) {
      if (moves.isNotEmpty || passives.isNotEmpty) {
        variations.add({
          'formName': formName,
          'moves': List<Map<String, dynamic>>.from(moves),
          'passives': List<Map<String, dynamic>>.from(passives),
        });
      }
      inVariation = false;
      formName = '';
      continue;
    }
    if (!inVariation) continue;

    if (line.startsWith('Sync Move:') || RegExp(r'^Move \d+:').hasMatch(line)) {
      final isSync = line.startsWith('Sync Move:');
      final slotMatch = RegExp(r'^Move (\d+):').firstMatch(line);
      final slot = slotMatch != null ? int.parse(slotMatch.group(1)!) : null;
      final moveName = isSync
          ? line.replaceFirst('Sync Move:', '').trim()
          : line.replaceFirst(RegExp(r'^Move \d+:\s*'), '').trim();
      String mType = '',
          mCat = '',
          mPower = '',
          mAcc = '',
          mGauge = '',
          mTarget = '',
          mDesc = '';
      for (int j = i + 1; j < lines.length; j++) {
        final ml = lines[j];
        if (ml.startsWith('Move ') ||
            ml.startsWith('Sync Move:') ||
            _passiveHeaderRegex.hasMatch(ml) ||
            ml.contains('Details') ||
            ml.startsWith('----'))
          break;
        if (ml.startsWith('Type:'))
          mType = ml.replaceFirst('Type:', '').trim();
        else if (ml.startsWith('Category:'))
          mCat = ml.replaceFirst('Category:', '').trim();
        else if (ml.startsWith('Description:'))
          mDesc = ml.replaceFirst('Description:', '').trim();
        else if (ml.startsWith('Power:')) {
          for (final a in ml.split('|').map((e) => e.trim())) {
            if (a.startsWith('Power:'))
              mPower = a.replaceFirst('Power:', '').trim();
            else if (a.startsWith('Accuracy:'))
              mAcc = a.replaceFirst('Accuracy:', '').trim();
            else if (a.startsWith('Gauge:'))
              mGauge = a.replaceFirst('Gauge:', '').trim();
            else if (a.startsWith('Target:'))
              mTarget = a.replaceFirst('Target:', '').trim();
          }
        }
      }
      moves.add({
        'name': moveName,
        'type': mType,
        'category': mCat,
        'power': mPower,
        'accuracy': mAcc,
        'gauge': mGauge,
        'target': mTarget,
        'description': mDesc,
        'isSync': isSync,
        'slot': slot,
      });
    } else if (_passiveHeaderRegex.hasMatch(line)) {
      final pName = line
          .replaceFirst(RegExp(r'^Passive \d+(?:\([^)]*\))?:\s*'), '')
          .trim();
      String pDesc = '';
      if (i + 1 < lines.length) {
        final pl = lines[i + 1].trim();
        if (pl.isNotEmpty &&
            !pl.startsWith('Passive ') &&
            !pl.startsWith('-') &&
            !pl.startsWith('Move') &&
            !pl.startsWith('Sync'))
          pDesc = pl;
      }
      passives.add({'name': pName, 'description': pDesc});
    }
  }
  if (inVariation && (moves.isNotEmpty || passives.isNotEmpty)) {
    variations.add({
      'formName': formName.isEmpty ? 'Variation' : formName,
      'moves': moves,
      'passives': passives,
    });
  }
  return variations;
}

List<String> splitByNoBlocks(String raw) {
  final lines = raw.split('\n');
  final sections = <String>[];
  final current = <String>[];
  for (final line in lines) {
    final trimmed = line.trim();
    if (trimmed.startsWith('No. ') && current.isNotEmpty) {
      sections.add(current.join('\n'));
      current.clear();
    }
    if (trimmed.startsWith('No. ') || current.isNotEmpty) current.add(line);
  }
  if (current.isNotEmpty) sections.add(current.join('\n'));
  return sections;
}
