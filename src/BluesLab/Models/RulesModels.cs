using System.Text.Json.Serialization;

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
    public bool AppliesToSync { get; set; }

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