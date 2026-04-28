enum EntityScope { self, ally, enemy, team, field }

enum EffectKind {
  tag,
  statModifier,
  powerModifier,
  damageModifier,
  rebuff,
  fieldEffect,
  passiveToggle,
}

enum ConditionKind {
  always,
  hpThreshold,
  fieldActive,
  moveCategory,
  moveType,
  teamHasTag,
  targetHasStatus,
  userHasStatus,
}

class PairTag {
  const PairTag({
    required this.category,
    required this.value,
    this.source = '',
  });

  final String category;
  final String value;
  final String source;

  String get key => '${category.toLowerCase()}:${value.toLowerCase()}';
}

class PassiveCondition {
  const PassiveCondition({
    required this.kind,
    this.subject,
    this.value,
    this.threshold,
  });

  final ConditionKind kind;
  final String? subject;
  final String? value;
  final double? threshold;
}

class PassiveEffect {
  const PassiveEffect({
    required this.kind,
    required this.scope,
    this.stat,
    this.value,
    this.flag,
  });

  final EffectKind kind;
  final EntityScope scope;
  final String? stat;
  final double? value;
  final String? flag;
}

class PassiveRule {
  const PassiveRule({
    this.conditions = const [],
    this.effects = const [],
  });

  final List<PassiveCondition> conditions;
  final List<PassiveEffect> effects;
}

class TeamSlotConfig {
  const TeamSlotConfig({
    required this.pairNumber,
    this.activeGridCells = const <int>{},
  });

  final int pairNumber;
  final Set<int> activeGridCells;
}

class TeamConfig {
  const TeamConfig({
    this.slots = const [],
    this.teamTags = const [],
    this.teamRules = const [],
  });

  final List<TeamSlotConfig> slots;
  final List<PairTag> teamTags;
  final List<PassiveRule> teamRules;
}
