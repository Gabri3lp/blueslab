using System.Text.Json.Serialization;

namespace BluesLab.Models;

public class TeamBattleState
{
    public List<CombatantState> Allies { get; set; } = new();
    public List<HashSet<long>> AllyActiveGrids { get; set; } = new();
    public int ActiveAttackerIndex { get; set; } = 0;
    public int AllySyncBuffs { get; set; } = 0;

    public List<CombatantState> Enemies { get; set; } = new();
    public int ActiveTargetIndex { get; set; } = 1; // Default to Center (Boss)
    public int EnemySyncBuffs { get; set; } = 0;

    // Allied Team Side Effects
    public bool AlliedPhysicalDamageReduction { get; set; }
    public bool AlliedSpecialDamageReduction { get; set; }

    // Enemy Opponents Side Effects
    public bool EnemyPhysicalDamageReduction { get; set; }
    public bool EnemySpecialDamageReduction { get; set; }
    public string EnemyDamageField { get; set; } = string.Empty;

    public FieldState Field { get; set; } = new();

    public string SelectedLeagueId { get; set; } = "circuit_1";
    public string SelectedFightId { get; set; } = "circuit_1_falkner";
    public StageFight? ActiveFight { get; set; }

    public TeamBattleState()
    {
        // 3 Allies
        for (int i = 0; i < 3; i++)
        {
            var ally = CombatantState.CreateAlly();
            ally.MoveLevel = 5;
            ally.SuperAwakeningLevel = 0;
            ally.HasExRole = false;
            ally.FormIndex = 0;
            Allies.Add(ally);
            AllyActiveGrids.Add(new HashSet<long>());
        }

        // 3 Enemies (Left=0, Center=1, Right=2)
        for (int i = 0; i < 3; i++)
        {
            var enemy = CombatantState.CreateEnemy();
            Enemies.Add(enemy);
        }

        // Initialize Team Circles
        foreach (var r in CombatantState.CircleRegions)
        {
            TeamCircles[r] = new Dictionary<string, bool>
            {
                ["physical"] = false,
                ["special"] = false,
                ["defensive"] = false
            };
            TeamCircleAllyCounts[r] = 1;
        }
    }

    public Dictionary<string, Dictionary<string, bool>> TeamCircles { get; set; } = new();
    public Dictionary<string, int> TeamCircleAllyCounts { get; set; } = new();

    public void ToggleCircle(string region, string circleType)
    {
        if (!TeamCircles.ContainsKey(region))
        {
            TeamCircles[region] = new Dictionary<string, bool> { ["physical"] = false, ["special"] = false, ["defensive"] = false };
        }
        TeamCircles[region][circleType] = !TeamCircles[region].GetValueOrDefault(circleType, false);
        UpdateCircleAllyCount(region);
    }

    public bool IsCircleActive(string region, string circleType)
    {
        return TeamCircles.TryGetValue(region, out var dict) && dict.GetValueOrDefault(circleType, false);
    }

    public int GetActiveCirclesCount()
    {
        return TeamCircles.Values.Sum(d => d.Values.Count(v => v));
    }

    public void ClearAllCircles()
    {
        foreach (var r in CombatantState.CircleRegions)
        {
            if (TeamCircles.ContainsKey(r))
            {
                TeamCircles[r]["physical"] = false;
                TeamCircles[r]["special"] = false;
                TeamCircles[r]["defensive"] = false;
            }
        }
    }

    public void UpdateCircleAllyCounts()
    {
        foreach (var r in CombatantState.CircleRegions)
        {
            UpdateCircleAllyCount(r);
        }
    }

    public int GetMatchingRegionAllies(string region)
    {
        return Allies.Count(a => a.Pair != null && MatchesTheme(a.Pair, region));
    }

    public int GetCircleBuffLevel(string region)
    {
        int count = GetMatchingRegionAllies(region);
        return Math.Clamp(count > 0 ? count : 1, 1, 3);
    }

    public void UpdateCircleAllyCount(string region)
    {
        TeamCircleAllyCounts[region] = GetCircleBuffLevel(region);
    }

    public CombatantState ActiveAttacker => Allies[Math.Clamp(ActiveAttackerIndex, 0, 2)];
    public HashSet<long> ActiveAttackerGrid => AllyActiveGrids[Math.Clamp(ActiveAttackerIndex, 0, 2)];
    public CombatantState ActiveTarget => Enemies[Math.Clamp(ActiveTargetIndex, 0, 2)];

    public static readonly Dictionary<string, string[]> RegionTrainers = new(StringComparer.OrdinalIgnoreCase)
    {
        ["Kanto"] = new[] { "Red", "Blue", "Leaf", "Brock", "Misty", "Lt. Surge", "Erika", "Koga", "Janine", "Sabrina", "Blaine", "Giovanni", "Lorelei", "Bruno", "Agatha", "Lance", "Bill", "Daisy", "Chase", "Elaine", "Oak", "Professor Oak", "Jessie", "James", "Ash" },
        ["Johto"] = new[] { "Ethan", "Lyra", "Kris", "Silver", "Falkner", "Bugsy", "Whitney", "Morty", "Chuck", "Jasmine", "Pryce", "Clair", "Will", "Karen", "Eusine", "Archer", "Ariana", "Petrel", "Proton" },
        ["Hoenn"] = new[] { "Brendan", "May", "Roxanne", "Brawly", "Wattson", "Flannery", "Norman", "Winona", "Tate", "Liza", "Wallace", "Juan", "Sidney", "Phoebe", "Glacia", "Drake", "Steven", "Zinnia", "Wally", "Archie", "Maxie", "Lisia", "Matt", "Courtney", "Shelly", "Tabitha", "Greta", "Lucy", "Anabel", "Noland", "Brandon" },
        ["Sinnoh"] = new[] { "Lucas", "Dawn", "Barry", "Roark", "Gardenia", "Maylene", "Crasher Wake", "Fantina", "Byron", "Candice", "Volkner", "Aaron", "Bertha", "Flint", "Lucian", "Cynthia", "Cyrus", "Mars", "Jupiter", "Saturn", "Riley", "Cheryl", "Mira", "Marley", "Buck", "Palmer", "Thorton", "Dahlia", "Darach", "Argenta", "Akari", "Rei", "Volo", "Irida", "Adaman", "Sabi", "Arezu", "Mai", "Looker" },
        ["Unova"] = new[] { "Hilbert", "Hilda", "Nate", "Rosa", "Cheren", "Bianca", "Cilan", "Chili", "Cress", "Lenora", "Burgh", "Elesa", "Clay", "Skyla", "Brycen", "Iris", "Drayden", "Roxie", "Marlon", "Shauntal", "Marshal", "Grimsley", "Caitlin", "Alder", "N", "Ghetsis", "Colress", "Hugh", "Emmet", "Ingo", "Bellelba", "Benga", "Brycen-Man" },
        ["Kalos"] = new[] { "Calem", "Serena", "Shauna", "Tierno", "Trevor", "Viola", "Grant", "Korrina", "Ramos", "Clemont", "Valerie", "Olympia", "Wulfric", "Malva", "Siebold", "Wikstrom", "Drasna", "Diantha", "Lysandre", "Sycamore", "Professor Sycamore", "Emma", "Evelyn", "Nita", "Dana", "Morgan", "Harmony", "Urbain", "Blossom", "Kali", "Katherine", "Linnea", "Helena", "Sina", "Dexio" },
        ["Alola"] = new[] { "Elio", "Selene", "Hau", "Gladion", "Lillie", "Ilima", "Lana", "Kiawe", "Mallow", "Sophocles", "Acerola", "Mina", "Hala", "Olivia", "Nanu", "Hapu", "Kahili", "Molayne", "Guzma", "Plumeria", "Kukui", "Burnet", "Lusamine", "Faba", "Ryuki", "The Masked Royal", "Samson Oak", "Naomi" },
        ["Galar"] = new[] { "Victor", "Gloria", "Hop", "Bede", "Marnie", "Milo", "Nessa", "Kabu", "Bea", "Allister", "Opal", "Gordie", "Melony", "Piers", "Raihan", "Klara", "Avery", "Mustard", "Peony", "Leon", "Sonia", "Oleana", "Rose", "Ball Guy", "Eve", "Petey" },
        ["Paldea"] = new[] { "Florian", "Juliana", "Nemona", "Arven", "Penny", "Katy", "Brassius", "Iono", "Kofu", "Larry", "Ryme", "Tulip", "Grusha", "Rika", "Poppy", "Hassel", "Geeta", "Clavell", "Jacq", "Dendra", "Miriam", "Raifort", "Saguaro", "Salvatore", "Tyme", "Atticus", "Mela", "Lacey", "Carmine", "Kieran", "Drayton", "Crispin", "Amarys", "Briar", "Teddy", "Eri", "Giacomo", "Ortega", "Clive", "Perrin" },
        ["Pasio"] = new[] { "Lear", "Rachel", "Sawyer", "Paulo", "Tina", "Bellis", "Main Character" }
    };

    private static readonly Dictionary<string, string> TrainerBaseToRegion = new(StringComparer.OrdinalIgnoreCase);

    private static readonly string[] TrainerPrefixes = new[]
    {
        "Sygna Suit (Ultimate)",
        "Sygna Suit",
        "Arc Suit",
        "Champion",
        "Classic",
        "Special Costume",
        "Holiday",
        "Palentine's",
        "Summer",
        "Fall",
        "Spring",
        "New Year's",
        "Anniversary",
        "Mix",
        "Professor"
    };

    static TeamBattleState()
    {
        foreach (var kvp in RegionTrainers)
        {
            foreach (var trainer in kvp.Value)
            {
                TrainerBaseToRegion[trainer] = kvp.Key;
            }
        }
    }

    /// <summary>
    /// Accurately resolves the official region of any Sync Pair in Pokémon Masters EX by extracting
    /// the base trainer name (stripping variant prefixes and costume parentheses).
    /// </summary>
    public static string? GetPairRegion(SyncPairDetail? pair)
    {
        if (pair == null) return null;

        string name = pair.TrainerName ?? string.Empty;
        if (string.IsNullOrWhiteSpace(name))
        {
            string d = pair.DisplayName ?? string.Empty;
            int amp = d.IndexOf('&');
            name = amp > 0 ? d.Substring(0, amp).Trim() : d.Trim();
        }

        int paren = name.IndexOf('(');
        if (paren >= 0)
        {
            name = name.Substring(0, paren).Trim();
        }

        bool stripped = true;
        while (stripped)
        {
            stripped = false;
            foreach (var pref in TrainerPrefixes)
            {
                if (name.StartsWith(pref, StringComparison.OrdinalIgnoreCase))
                {
                    name = name.Substring(pref.Length).Trim();
                    stripped = true;
                }
            }
        }

        if (TrainerBaseToRegion.TryGetValue(name, out var reg))
            return reg;

        return null;
    }

    public static bool MatchesTheme(SyncPairDetail? pair, string theme)
    {
        if (pair == null || string.IsNullOrWhiteSpace(theme)) return false;

        // 1. Type check (for Arc Suit Myths and Type Master Passives)
        if (string.Equals(pair.Type, theme, StringComparison.OrdinalIgnoreCase))
            return true;

        // 2. Exact Region check (for Regional Pride, Spirit, Flag Bearer)
        string? pairRegion = GetPairRegion(pair);
        if (!string.IsNullOrEmpty(pairRegion) && string.Equals(pairRegion, theme, StringComparison.OrdinalIgnoreCase))
            return true;

        return false;
    }

    /// <summary>
    /// Calculates the number of allies (other than the owner itself) that share the same region or theme for Master Passives.
    /// </summary>
    public int GetMasterPassiveAllyCount(string theme, int ownerIndex = -1)
    {
        int count = 0;
        int targetOwner = ownerIndex >= 0 ? ownerIndex : ActiveAttackerIndex;
        for (int i = 0; i < 3; i++)
        {
            if (i == targetOwner) continue;
            var other = Allies[i];
            if (other.Pair == null) continue;

            if (MatchesTheme(other.Pair, theme)) count++;
        }
        return Math.Clamp(count, 0, 2);
    }
}