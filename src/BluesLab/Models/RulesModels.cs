using System.Text.Json.Serialization;
using BluesLab.Services;

namespace BluesLab.Models;

public class DamageRulesDocument
{
    [JsonPropertyName("moveScaling")]
    public List<MoveScalingRule> MoveScaling { get; set; } = new();

    [JsonPropertyName("damagePassives")]
    public List<DamagePassiveRule> DamagePassives { get; set; } = new();

    [JsonPropertyName("masterPassives")]
    public List<MasterPassiveRule> MasterPassives { get; set; } = new();

    [JsonPropertyName("luckySkills")]
    public List<LuckySkillRule> LuckySkills { get; set; } = new();
}

public class MoveScalingRule
{
    [JsonPropertyName("syncPair")]
    public string SyncPair { get; set; } = string.Empty;

    [JsonPropertyName("moveName")]
    public string MoveName { get; set; } = string.Empty;

    [JsonPropertyName("stat")]
    public string Stat { get; set; } = string.Empty;

    [JsonPropertyName("who")]
    public string Who { get; set; } = "user";

    [JsonPropertyName("direction")]
    public string Direction { get; set; } = "raised";

    [JsonPropertyName("stepPer1000")]
    public int StepPer1000 { get; set; }

    [JsonPropertyName("thresholdTable")]
    public List<ThresholdEntryItem> ThresholdTable { get; set; } = new();

    [JsonPropertyName("capPer1000")]
    public int CapPer1000 { get; set; }
}

public class ThresholdEntryItem
{
    [JsonPropertyName("minPct")]
    public int MinPct { get; set; }

    [JsonPropertyName("multiplierPer1000")]
    public int MultiplierPer1000 { get; set; }
}

public class DamagePassiveRule
{
    [JsonPropertyName("source")]
    public string Source { get; set; } = string.Empty;

    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    [JsonPropertyName("applies_to")]
    public string AppliesTo { get; set; } = string.Empty;

    [JsonPropertyName("affects")]
    public string Affects { get; set; } = string.Empty;

    [JsonPropertyName("mechanism")]
    public string Mechanism { get; set; } = string.Empty;

    [JsonPropertyName("value")]
    public int Value { get; set; }

    [JsonPropertyName("stat")]
    public string Stat { get; set; } = string.Empty;

    [JsonPropertyName("stat_target")]
    public string StatTarget { get; set; } = string.Empty;

    [JsonPropertyName("conditions")]
    public List<List<string>> Conditions { get; set; } = new();

    [JsonPropertyName("move_name")]
    public string MoveName { get; set; } = string.Empty;

    [JsonPropertyName("sub_passives")]
    public List<DamagePassiveRule> SubPassives { get; set; } = new();
}

public class MasterPassiveRule
{
    [JsonPropertyName("syncPair")]
    public string SyncPair { get; set; } = string.Empty;

    [JsonPropertyName("passiveName")]
    public string PassiveName { get; set; } = string.Empty;

    [JsonPropertyName("theme")]
    public string Theme { get; set; } = string.Empty;

    [JsonPropertyName("category")]
    public string Category { get; set; } = "any";

    [JsonPropertyName("appliesToSync")]
    public bool AppliesToSync { get; set; } = true;

    [JsonPropertyName("basePowerUpPct")]
    public int BasePowerUpPct { get; set; } = 10;

    [JsonPropertyName("perAdditionalAllyPct")]
    public int PerAdditionalAllyPct { get; set; } = 5;

    [JsonPropertyName("maxPowerUpPct")]
    public int MaxPowerUpPct { get; set; } = 20;

    public double PowerUpForAdditionalAllies(int additionalAllies)
    {
        int extra = Math.Clamp(additionalAllies, 0, 2);
        int powerUp = BasePowerUpPct + PerAdditionalAllyPct * extra;
        int capped = powerUp > MaxPowerUpPct ? MaxPowerUpPct : powerUp;
        return capped / 100.0;
    }

    public bool AppliesToMove(MoveItem move)
    {
        if (!MoveScopeRules.AllowsMasterPassives(move)) return false;
        bool isPhysical = string.Equals(move.Category, "Physical", StringComparison.OrdinalIgnoreCase);
        bool isSpecial = string.Equals(move.Category, "Special", StringComparison.OrdinalIgnoreCase);
        if (move.IsSync && !AppliesToSync) return false;
        return Category.ToLowerInvariant() switch
        {
            "physical" => isPhysical,
            "special" => isSpecial,
            _ => true
        };
    }

    private static readonly string[] MasterRegions = new[]
    {
        "Kanto", "Johto", "Hoenn", "Sinnoh", "Unova", "Kalos", "Alola", "Galar", "Paldea", "Pasio"
    };

    private static readonly string[] MasterTypes = new[]
    {
        "Normal", "Fire", "Water", "Electric", "Grass", "Ice", "Fighting", "Poison",
        "Ground", "Flying", "Psychic", "Bug", "Rock", "Ghost", "Dragon", "Dark", "Steel", "Fairy"
    };

    public static List<MasterPassiveRule> ExtractMasterPassives(SyncPairDetail? pair, DamageRulesDocument? rules = null)
    {
        var list = new List<MasterPassiveRule>();
        if (pair == null) return list;

        if (rules != null && rules.MasterPassives.Count > 0)
        {
            list.AddRange(rules.MasterPassives.Where(m =>
                string.Equals(m.SyncPair, pair.DisplayName, StringComparison.OrdinalIgnoreCase) ||
                (!string.IsNullOrEmpty(pair.DisplayName) && m.SyncPair.StartsWith(pair.DisplayName, StringComparison.OrdinalIgnoreCase))));
        }

        foreach (var p in pair.Passives)
        {
            string name = p.Name?.Trim() ?? string.Empty;
            if (string.IsNullOrEmpty(name)) continue;

            if (list.Any(x => string.Equals(x.PassiveName, name, StringComparison.OrdinalIgnoreCase)))
                continue;

            // 1. Regional Pride, Spirit, Flag Bearer / Flagbearer
            bool matchedStandard = false;
            foreach (var r in MasterRegions)
            {
                if (name.Equals($"{r} Pride", StringComparison.OrdinalIgnoreCase))
                {
                    list.Add(new MasterPassiveRule
                    {
                        SyncPair = pair.DisplayName,
                        PassiveName = name,
                        Theme = r,
                        Category = "physical",
                        AppliesToSync = true,
                        BasePowerUpPct = 20,
                        PerAdditionalAllyPct = 15,
                        MaxPowerUpPct = 50
                    });
                    matchedStandard = true;
                    break;
                }
                else if (name.Equals($"{r} Spirit", StringComparison.OrdinalIgnoreCase))
                {
                    list.Add(new MasterPassiveRule
                    {
                        SyncPair = pair.DisplayName,
                        PassiveName = name,
                        Theme = r,
                        Category = "special",
                        AppliesToSync = true,
                        BasePowerUpPct = 20,
                        PerAdditionalAllyPct = 15,
                        MaxPowerUpPct = 50
                    });
                    matchedStandard = true;
                    break;
                }
                else if (name.Equals($"{r} Flag Bearer", StringComparison.OrdinalIgnoreCase) ||
                         name.Equals($"{r} Flagbearer", StringComparison.OrdinalIgnoreCase))
                {
                    list.Add(new MasterPassiveRule
                    {
                        SyncPair = pair.DisplayName,
                        PassiveName = name,
                        Theme = r,
                        Category = "any",
                        AppliesToSync = true,
                        BasePowerUpPct = 10,
                        PerAdditionalAllyPct = 10,
                        MaxPowerUpPct = 30
                    });
                    matchedStandard = true;
                    break;
                }
            }
            if (matchedStandard) continue;

            // 2. Type Teamwork
            bool matchedTeamwork = false;
            foreach (var t in MasterTypes)
            {
                if (name.Equals($"{t} Teamwork", StringComparison.OrdinalIgnoreCase))
                {
                    list.Add(new MasterPassiveRule
                    {
                        SyncPair = pair.DisplayName,
                        PassiveName = name,
                        Theme = t,
                        Category = "any",
                        AppliesToSync = true,
                        BasePowerUpPct = 10,
                        PerAdditionalAllyPct = 5,
                        MaxPowerUpPct = 20
                    });
                    matchedTeamwork = true;
                    break;
                }
            }
            if (matchedTeamwork) continue;

            // 3. Arc Suit Myth
            if (name.EndsWith(" Myth", StringComparison.OrdinalIgnoreCase))
            {
                list.Add(new MasterPassiveRule
                {
                    SyncPair = pair.DisplayName,
                    PassiveName = name,
                    Theme = pair.Type,
                    Category = "any",
                    AppliesToSync = true,
                    BasePowerUpPct = 10,
                    PerAdditionalAllyPct = 10,
                    MaxPowerUpPct = 30
                });
                continue;
            }

            // 4. EX Master Passives (Pokéfestival Maestro EX / Master Fair EX)
            // Child passive IDs 28030101 to 28031001 define the regional EX Master Passives.
            string? exRegion = null;
            if (p.ChildPassives != null)
            {
                foreach (var cp in p.ChildPassives)
                {
                    if (cp.Id >= 28030101 && cp.Id <= 28031001)
                    {
                        int regIdx = (int)((cp.Id - 28030001) / 100);
                        if (regIdx >= 1 && regIdx <= MasterRegions.Length)
                        {
                            exRegion = MasterRegions[regIdx - 1];
                            break;
                        }
                    }
                }
            }

            if (string.IsNullOrEmpty(exRegion))
            {
                string desc = p.Description ?? string.Empty;
                if ((p.Id >= 28040000 && p.Id < 28050000) ||
                    (desc.Contains("all allied sync pairs", StringComparison.OrdinalIgnoreCase) &&
                     desc.Contains("20%", StringComparison.OrdinalIgnoreCase) &&
                     desc.Contains("15%", StringComparison.OrdinalIgnoreCase) &&
                     desc.Contains("50%", StringComparison.OrdinalIgnoreCase)))
                {
                    exRegion = MasterRegions.FirstOrDefault(r => TeamBattleState.MatchesTheme(pair, r)) ?? "Kanto";
                }
            }

            if (!string.IsNullOrEmpty(exRegion))
            {
                list.Add(new MasterPassiveRule
                {
                    SyncPair = pair.DisplayName,
                    PassiveName = name,
                    Theme = exRegion,
                    Category = "any",
                    AppliesToSync = true,
                    BasePowerUpPct = 20,
                    PerAdditionalAllyPct = 15,
                    MaxPowerUpPct = 50
                });
            }
        }

        return list;
    }
}

public class LuckySkillRule
{
    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("restricted_to_roles")]
    public List<string>? RestrictedToRoles { get; set; }

    [JsonPropertyName("restricted_to_pairs")]
    public List<string>? RestrictedToPairs { get; set; }

    public bool IsAvailableFor(string role, string pairName = "")
    {
        if (RestrictedToPairs != null && RestrictedToPairs.Count > 0)
        {
            return RestrictedToPairs.Any(p => string.Equals(p, pairName, StringComparison.OrdinalIgnoreCase));
        }
        if (RestrictedToRoles != null && RestrictedToRoles.Count > 0)
        {
            return RestrictedToRoles.Any(r => string.Equals(r, role, StringComparison.OrdinalIgnoreCase));
        }
        return true;
    }
}