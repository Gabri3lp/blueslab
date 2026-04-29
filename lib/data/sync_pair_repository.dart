import 'dart:convert';

import 'package:flutter/services.dart';

import '../models/future_rules.dart';
import '../models/sync_pair_models.dart';

class SyncPairRepository {
  const SyncPairRepository();

  Future<ParsedData> load() async {
    final jsonStr = await rootBundle.loadString('assets/data/sync_pairs.json');
    final jsonList = json.decode(jsonStr) as List<dynamic>;

    final pairs =
        jsonList
            .map((entry) => _parsePair(entry as Map<String, dynamic>))
            .toList()
          ..sort((left, right) {
            final leftDate = left.releaseDate ?? DateTime(2000);
            final rightDate = right.releaseDate ?? DateTime(2000);
            return rightDate.compareTo(leftDate);
          });

    return ParsedData(pairs: pairs);
  }

  SyncPairData _parsePair(Map<String, dynamic> jsonMap) {
    final pairType = (jsonMap['type'] ?? '') as String;
    final pairRole = (jsonMap['role'] ?? '') as String;
    final exRole = (jsonMap['exRole'] ?? '') as String;
    final weakness = (jsonMap['weakness'] ?? '') as String;

    final cells = (jsonMap['cells'] as List? ?? const [])
        .map((entry) => _parseCell(entry as Map<String, dynamic>))
        .toList();

    final moves = (jsonMap['moves'] as List? ?? const [])
        .map(
          (entry) =>
              _parseMove(entry as Map<String, dynamic>, pairType: pairType),
        )
        .toList();

    final passives = (jsonMap['passives'] as List? ?? const [])
        .map((entry) => _parsePassive(entry as Map<String, dynamic>))
        .toList();

    final teraPassives = (jsonMap['teraPassives'] as List? ?? const [])
        .map((entry) => _parsePassive(entry as Map<String, dynamic>))
        .toList();

    final pairTags = <PairTag>[
      if (pairType.isNotEmpty) PairTag(category: 'type', value: pairType),
      if (pairRole.isNotEmpty) PairTag(category: 'role', value: pairRole),
      if (exRole.isNotEmpty) PairTag(category: 'ex_role', value: exRole),
      if (weakness.isNotEmpty) PairTag(category: 'weakness', value: weakness),
      ..._extractThemeTags(jsonMap),
      ..._extractMoveEffectTags(moves),
      ..._extractPassiveTags(passives),
    ];

    final rules = [
      for (final passive in passives) passive.rule,
      for (final passive in teraPassives) passive.rule,
    ];

    return SyncPairData(
      number: (jsonMap['number'] as num?)?.toInt() ?? 0,
      displayName: (jsonMap['displayName'] ?? '') as String,
      role: pairRole,
      exRole: exRole,
      type: pairType,
      weakness: weakness,
      rarity: (jsonMap['rarity'] as num?)?.toInt() ?? 5,
      hasEx: jsonMap['hasEx'] == true,
      cells: cells,
      releaseDate: DateTime.tryParse((jsonMap['releaseDate'] ?? '') as String),
      syncMoveName: (jsonMap['syncMoveName'] ?? '') as String,
      moves: moves,
      passives: passives,
      description: '',
      hasTera: jsonMap['hasTera'] == true,
      teraMove: _parseOptionalMove(jsonMap['teraMove'], pairType: pairType),
      teraPassives: teraPassives,
      stats: _parseNestedStats(jsonMap['stats'] as Map<String, dynamic>?),
      teraStatMultiplier: _parseTeraStatMultiplier(jsonMap),
      megaStatMultiplier: _parseMegaStatMultiplier(
        jsonMap['megaStatMultiplier'] as Map<String, dynamic>?,
      ),
      megaStats: _parseNestedStats(
        jsonMap['megaStats'] as Map<String, dynamic>?,
      ),
      formStats: _parseFormStats(jsonMap['formStats'] as Map<String, dynamic>?),
      variations: _parseVariations(jsonMap['variations'] as List?),
      tags: _dedupeTags(pairTags),
      rules: rules
          .where(
            (rule) => rule.conditions.isNotEmpty || rule.effects.isNotEmpty,
          )
          .toList(),
    );
  }

  GridCellData _parseCell(Map<String, dynamic> jsonMap) {
    final title = (jsonMap['title'] ?? '') as String;
    final colorKind = (jsonMap['colorKind'] ?? 'Unknown') as String;

    return GridCellData(
      cellNumber: (jsonMap['cellNumber'] as num?)?.toInt() ?? 0,
      q: (jsonMap['q'] as num?)?.toInt() ?? 0,
      r: (jsonMap['r'] as num?)?.toInt() ?? 0,
      s: (jsonMap['s'] as num?)?.toInt() ?? 0,
      energyCost: (jsonMap['energyCost'] as num?)?.toInt() ?? 0,
      orbCost: (jsonMap['orbCost'] as num?)?.toInt() ?? 0,
      title: title,
      description: (jsonMap['description'] ?? '') as String,
      colorKind: colorKind,
      moveLevel: (jsonMap['moveLevel'] as num?)?.toInt() ?? 1,
      tags: _dedupeTags([
        PairTag(category: 'grid_kind', value: colorKind),
        ..._tileTags(title, colorKind),
      ]),
      effects: _tileEffects(title, colorKind),
    );
  }

  MoveData _parseMove(
    Map<String, dynamic> jsonMap, {
    required String pairType,
  }) {
    final name = (jsonMap['name'] ?? '') as String;
    final type = (jsonMap['type'] ?? '') as String;
    final category = (jsonMap['category'] ?? '') as String;
    final description = (jsonMap['description'] ?? '') as String;

    return MoveData(
      name: name,
      type: type,
      category: category,
      power: (jsonMap['power'] ?? '') as String,
      accuracy: (jsonMap['accuracy'] ?? '') as String,
      gauge: (jsonMap['gauge'] ?? '') as String,
      target: (jsonMap['target'] ?? '') as String,
      description: description,
      isSync: jsonMap['isSync'] == true,
      slot: jsonMap['slot'] as int?,
      tags: _dedupeTags([
        if (type.isNotEmpty) PairTag(category: 'move_type', value: type),
        if (category.isNotEmpty)
          PairTag(category: 'move_category', value: category),
        if (name.isNotEmpty) PairTag(category: 'move_name', value: name),
        if (type.isNotEmpty && type == pairType)
          PairTag(category: 'stab', value: 'true'),
        ..._effectTagsFromText(description),
      ]),
      effects: _effectsFromMoveDescription(description),
    );
  }

  MoveData? _parseOptionalMove(dynamic raw, {required String pairType}) {
    if (raw is! Map<String, dynamic>) {
      return null;
    }
    return _parseMove(raw, pairType: pairType);
  }

  PassiveData _parsePassive(Map<String, dynamic> jsonMap) {
    final name = (jsonMap['name'] ?? '') as String;
    final description = (jsonMap['description'] ?? '') as String;
    return PassiveData(
      name: name,
      description: description,
      tags: _dedupeTags([
        PairTag(category: 'passive_name', value: name),
        ..._effectTagsFromText(name),
        ..._effectTagsFromText(description),
      ]),
      rule: _ruleFromPassiveText(name, description),
    );
  }

  List<VariationData> _parseVariations(List? rawList) {
    return (rawList ?? const []).map((entry) {
      final variation = entry as Map<String, dynamic>;
      final moves = (variation['moves'] as List? ?? const [])
          .map(
            (move) => _parseMove(
              move as Map<String, dynamic>,
              pairType: (move['type'] ?? '') as String,
            ),
          )
          .toList();
      final passives = (variation['passives'] as List? ?? const [])
          .map((passive) => _parsePassive(passive as Map<String, dynamic>))
          .toList();
      return VariationData(
        formName: (variation['formName'] ?? 'Variation') as String,
        moves: moves,
        passives: passives,
      );
    }).toList();
  }

  Map<String, Map<String, int>> _parseNestedStats(Map<String, dynamic>? raw) {
    final result = <String, Map<String, int>>{};
    for (final entry in (raw ?? const <String, dynamic>{}).entries) {
      final valueMap = entry.value as Map<String, dynamic>;
      result[entry.key] = valueMap.map(
        (key, value) => MapEntry(key, (value as num).toInt()),
      );
    }
    return result;
  }

  Map<String, Map<String, Map<String, int>>> _parseFormStats(
    Map<String, dynamic>? raw,
  ) {
    final result = <String, Map<String, Map<String, int>>>{};
    for (final entry in (raw ?? const <String, dynamic>{}).entries) {
      result[entry.key] = _parseNestedStats(
        entry.value as Map<String, dynamic>?,
      );
    }
    return result;
  }

  Map<String, double> _parseDoubleMap(Map<String, dynamic>? raw) {
    return (raw ?? const <String, dynamic>{}).map(
      (key, value) => MapEntry(key, (value as num).toDouble()),
    );
  }

  Map<String, double> _parseMegaStatMultiplier(Map<String, dynamic>? raw) {
    return (raw ?? const <String, dynamic>{}).map((key, value) {
      final parsed = (value as num).toDouble();
      return MapEntry(key, double.parse(parsed.toStringAsFixed(2)));
    });
  }

  Map<String, double> _parseTeraStatMultiplier(Map<String, dynamic> jsonMap) {
    final result = <String, double>{};

    final teraPassives = jsonMap['teraPassives'] as List? ?? const [];
    for (final entry in teraPassives) {
      final passive = entry as Map<String, dynamic>;
      final name = (passive['name'] ?? '') as String;
      final match = RegExp(
        r'While S-Tera:\s*(\d)\s*Stats.*?(\d+)$',
      ).firstMatch(name);
      if (match == null) {
        continue;
      }

      final statCount = int.parse(match.group(1)!);
      final bonusValue = int.parse(match.group(2)!);
      final multiplier = 1.0 + bonusValue * 0.1;
      if (statCount == 5) {
        for (final stat in ['atk', 'def', 'spa', 'spd', 'spe']) {
          result[stat] = multiplier;
        }
      }
    }

    result.addAll(
      _parseDoubleMap(jsonMap['teraStatMultiplier'] as Map<String, dynamic>?),
    );
    return result;
  }

  List<PairTag> _extractThemeTags(Map<String, dynamic> jsonMap) {
    final output = <PairTag>[];
    final textFields = <String>[
      (jsonMap['displayName'] ?? '') as String,
      for (final move in jsonMap['moves'] as List? ?? const [])
        (move as Map<String, dynamic>)['description'] as String? ?? '',
      for (final passive in jsonMap['passives'] as List? ?? const [])
        (passive as Map<String, dynamic>)['description'] as String? ?? '',
    ];

    for (final text in textFields) {
      final lower = text.toLowerCase();
      if (lower.contains('kanto')) {
        output.add(const PairTag(category: 'theme_skill', value: 'Kanto'));
      }
      if (lower.contains('johto')) {
        output.add(const PairTag(category: 'theme_skill', value: 'Johto'));
      }
      if (lower.contains('paldea')) {
        output.add(const PairTag(category: 'theme_skill', value: 'Paldea'));
      }
      if (lower.contains('pasio')) {
        output.add(const PairTag(category: 'theme_skill', value: 'Pasio'));
      }
    }
    return output;
  }

  List<PairTag> _extractMoveEffectTags(List<MoveData> moves) {
    return [for (final move in moves) ...move.tags];
  }

  List<PairTag> _extractPassiveTags(List<PassiveData> passives) {
    return [for (final passive in passives) ...passive.tags];
  }

  List<PairTag> _effectTagsFromText(String text) {
    final lower = text.toLowerCase();
    final tags = <PairTag>[];

    void addIfFound(String needle, String category, String value) {
      if (lower.contains(needle)) {
        tags.add(PairTag(category: category, value: value));
      }
    }

    addIfFound('burn', 'effect', 'burn');
    addIfFound('sleep', 'effect', 'sleep');
    addIfFound('freeze', 'effect', 'freeze');
    addIfFound('paraly', 'effect', 'paralysis');
    addIfFound('poison', 'effect', 'poison');
    addIfFound('confus', 'effect', 'confusion');
    addIfFound('flinch', 'effect', 'flinch');
    addIfFound('trap', 'effect', 'trap');
    addIfFound('restrain', 'effect', 'restrain');
    addIfFound('lowers the target', 'effect', 'debuff');
    addIfFound('raises the user', 'effect', 'self_buff');
    addIfFound('raises the allied field', 'effect', 'field_buff');
    addIfFound('zone', 'field', 'zone');
    addIfFound('terrain', 'field', 'terrain');
    addIfFound('weather', 'field', 'weather');
    addIfFound('circle', 'field', 'circle');

    return tags;
  }

  List<PairTag> _tileTags(String title, String colorKind) {
    final tags = <PairTag>[PairTag(category: 'grid_kind', value: colorKind)];
    final lower = title.toLowerCase();
    if (lower.contains('power')) {
      tags.add(const PairTag(category: 'tile_effect', value: 'power'));
    }
    if (lower.contains('accuracy')) {
      tags.add(const PairTag(category: 'tile_effect', value: 'accuracy'));
    }
    if (lower.contains('refresh')) {
      tags.add(const PairTag(category: 'tile_effect', value: 'refresh'));
    }
    if (lower.contains('move gauge')) {
      tags.add(const PairTag(category: 'tile_effect', value: 'gauge'));
    }
    return tags;
  }

  List<PassiveEffect> _tileEffects(String title, String colorKind) {
    final lower = title.toLowerCase();
    final effects = <PassiveEffect>[];
    final powerMatch = RegExp(r'power\s+(\d+)').firstMatch(lower);
    if (powerMatch != null) {
      effects.add(
        PassiveEffect(
          kind: EffectKind.powerModifier,
          scope: EntityScope.self,
          value: double.parse(powerMatch.group(1)!),
          flag: colorKind,
        ),
      );
    }
    return effects;
  }

  List<PassiveEffect> _effectsFromMoveDescription(String description) {
    final lower = description.toLowerCase();
    final effects = <PassiveEffect>[];
    if (lower.contains('lowers the target')) {
      effects.add(
        const PassiveEffect(
          kind: EffectKind.statModifier,
          scope: EntityScope.enemy,
          flag: 'debuff',
        ),
      );
    }
    if (lower.contains('raises the user')) {
      effects.add(
        const PassiveEffect(
          kind: EffectKind.statModifier,
          scope: EntityScope.self,
          flag: 'self_buff',
        ),
      );
    }
    if (lower.contains('weather') ||
        lower.contains('terrain') ||
        lower.contains('zone')) {
      effects.add(
        const PassiveEffect(
          kind: EffectKind.fieldEffect,
          scope: EntityScope.field,
        ),
      );
    }
    return effects;
  }

  PassiveRule _ruleFromPassiveText(String name, String description) {
    final text = '$name $description'.toLowerCase();
    final conditions = <PassiveCondition>[];
    final effects = <PassiveEffect>[];

    if (text.contains('when it enters a battle')) {
      conditions.add(
        const PassiveCondition(
          kind: ConditionKind.always,
          subject: 'battle_entry',
        ),
      );
    }
    if (text.contains('while') && text.contains('weather')) {
      conditions.add(
        const PassiveCondition(
          kind: ConditionKind.fieldActive,
          value: 'weather',
        ),
      );
    }
    if (text.contains('while') && text.contains('terrain')) {
      conditions.add(
        const PassiveCondition(
          kind: ConditionKind.fieldActive,
          value: 'terrain',
        ),
      );
    }
    if (text.contains('while') && text.contains('zone')) {
      conditions.add(
        const PassiveCondition(kind: ConditionKind.fieldActive, value: 'zone'),
      );
    }
    if (text.contains('burned')) {
      conditions.add(
        const PassiveCondition(
          kind: ConditionKind.userHasStatus,
          value: 'burned',
        ),
      );
    }

    if (text.contains('raises')) {
      effects.add(
        const PassiveEffect(
          kind: EffectKind.statModifier,
          scope: EntityScope.self,
        ),
      );
    }
    if (text.contains('powers up')) {
      effects.add(
        const PassiveEffect(
          kind: EffectKind.powerModifier,
          scope: EntityScope.self,
        ),
      );
    }
    if (text.contains('team') || text.contains('allied')) {
      effects.add(
        const PassiveEffect(
          kind: EffectKind.passiveToggle,
          scope: EntityScope.team,
        ),
      );
    }

    return PassiveRule(conditions: conditions, effects: effects);
  }

  List<PairTag> _dedupeTags(List<PairTag> tags) {
    final byKey = <String, PairTag>{};
    for (final tag in tags) {
      byKey[tag.key] = tag;
    }
    return byKey.values.toList();
  }
}
