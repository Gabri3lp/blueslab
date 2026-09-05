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

    public FieldState Field { get; set; } = new();

    public string SelectedLeagueId { get; set; } = "circuit_1";
    public string SelectedFightId { get; set; } = "circuit_1_falkner";
    public StageFight? ActiveFight { get; set; }

    public void SetFullGridForAlly(int slot)
    {
        if (slot < 0 || slot >= Allies.Count) return;
        var ally = Allies[slot];
        if (ally.Pair?.Grid == null) return;
        AllyActiveGrids[slot].Clear();
        foreach (var cell in ally.Pair.Grid)
        {
            if (cell.PowerBonus.Count > 0 || cell.StatBonus.Count > 0 || !string.IsNullOrEmpty(cell.Title))
            {
                AllyActiveGrids[slot].Add(cell.CellId);
            }
        }
    }

    public void ClearGridForAlly(int slot)
    {
        if (slot >= 0 && slot < AllyActiveGrids.Count)
        {
            AllyActiveGrids[slot].Clear();
        }
    }

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
    }

    public CombatantState ActiveAttacker => Allies[Math.Clamp(ActiveAttackerIndex, 0, 2)];
    public HashSet<long> ActiveAttackerGrid => AllyActiveGrids[Math.Clamp(ActiveAttackerIndex, 0, 2)];
    public CombatantState ActiveTarget => Enemies[Math.Clamp(ActiveTargetIndex, 0, 2)];

    /// <summary>
    /// Calculates the number of allies (other than the attacker itself) that share the same region or theme for Master Passives.
    /// </summary>
    public int GetMasterPassiveAllyCount(string passiveName)
    {
        if (ActiveAttacker.Pair == null) return 0;
        int count = 0;
        for (int i = 0; i < 3; i++)
        {
            if (i == ActiveAttackerIndex) continue;
            var other = Allies[i];
            if (other.Pair == null) continue;

            string dName = other.Pair.DisplayName;
            // Check if other pair matches region / theme of passive
            if (passiveName.Contains("Kanto", StringComparison.OrdinalIgnoreCase) && (dName.Contains("Red", StringComparison.OrdinalIgnoreCase) || dName.Contains("Blue", StringComparison.OrdinalIgnoreCase) || dName.Contains("Leaf", StringComparison.OrdinalIgnoreCase) || dName.Contains("Brock", StringComparison.OrdinalIgnoreCase) || dName.Contains("Misty", StringComparison.OrdinalIgnoreCase) || dName.Contains("Erika", StringComparison.OrdinalIgnoreCase) || dName.Contains("Sabrina", StringComparison.OrdinalIgnoreCase) || dName.Contains("Giovanni", StringComparison.OrdinalIgnoreCase))) count++;
            else if (passiveName.Contains("Johto", StringComparison.OrdinalIgnoreCase) && (dName.Contains("Ethan", StringComparison.OrdinalIgnoreCase) || dName.Contains("Lyra", StringComparison.OrdinalIgnoreCase) || dName.Contains("Kris", StringComparison.OrdinalIgnoreCase) || dName.Contains("Silver", StringComparison.OrdinalIgnoreCase) || dName.Contains("Morty", StringComparison.OrdinalIgnoreCase) || dName.Contains("Whitney", StringComparison.OrdinalIgnoreCase) || dName.Contains("Clair", StringComparison.OrdinalIgnoreCase) || dName.Contains("Lance", StringComparison.OrdinalIgnoreCase))) count++;
            else if (passiveName.Contains("Hoenn", StringComparison.OrdinalIgnoreCase) && (dName.Contains("Brendan", StringComparison.OrdinalIgnoreCase) || dName.Contains("May", StringComparison.OrdinalIgnoreCase) || dName.Contains("Steven", StringComparison.OrdinalIgnoreCase) || dName.Contains("Zinnia", StringComparison.OrdinalIgnoreCase) || dName.Contains("Wally", StringComparison.OrdinalIgnoreCase) || dName.Contains("Archie", StringComparison.OrdinalIgnoreCase) || dName.Contains("Maxie", StringComparison.OrdinalIgnoreCase))) count++;
            else if (passiveName.Contains("Sinnoh", StringComparison.OrdinalIgnoreCase) && (dName.Contains("Lucas", StringComparison.OrdinalIgnoreCase) || dName.Contains("Dawn", StringComparison.OrdinalIgnoreCase) || dName.Contains("Cynthia", StringComparison.OrdinalIgnoreCase) || dName.Contains("Barry", StringComparison.OrdinalIgnoreCase) || dName.Contains("Volkner", StringComparison.OrdinalIgnoreCase) || dName.Contains("Cyrus", StringComparison.OrdinalIgnoreCase))) count++;
            else if (passiveName.Contains("Unova", StringComparison.OrdinalIgnoreCase) && (dName.Contains("Hilbert", StringComparison.OrdinalIgnoreCase) || dName.Contains("Hilda", StringComparison.OrdinalIgnoreCase) || dName.Contains("Nate", StringComparison.OrdinalIgnoreCase) || dName.Contains("Rosa", StringComparison.OrdinalIgnoreCase) || dName.Contains("N", StringComparison.OrdinalIgnoreCase) || dName.Contains("Iris", StringComparison.OrdinalIgnoreCase) || dName.Contains("Elesa", StringComparison.OrdinalIgnoreCase) || dName.Contains("Skyla", StringComparison.OrdinalIgnoreCase) || dName.Contains("Ghetsis", StringComparison.OrdinalIgnoreCase))) count++;
            else if (passiveName.Contains("Kalos", StringComparison.OrdinalIgnoreCase) && (dName.Contains("Calem", StringComparison.OrdinalIgnoreCase) || dName.Contains("Serena", StringComparison.OrdinalIgnoreCase) || dName.Contains("Diantha", StringComparison.OrdinalIgnoreCase) || dName.Contains("Korrina", StringComparison.OrdinalIgnoreCase) || dName.Contains("Lysandre", StringComparison.OrdinalIgnoreCase) || dName.Contains("Sycamore", StringComparison.OrdinalIgnoreCase))) count++;
            else if (passiveName.Contains("Alola", StringComparison.OrdinalIgnoreCase) && (dName.Contains("Elio", StringComparison.OrdinalIgnoreCase) || dName.Contains("Selene", StringComparison.OrdinalIgnoreCase) || dName.Contains("Lillie", StringComparison.OrdinalIgnoreCase) || dName.Contains("Gladion", StringComparison.OrdinalIgnoreCase) || dName.Contains("Lusamine", StringComparison.OrdinalIgnoreCase) || dName.Contains("Hau", StringComparison.OrdinalIgnoreCase) || dName.Contains("Acerola", StringComparison.OrdinalIgnoreCase))) count++;
            else if (passiveName.Contains("Galar", StringComparison.OrdinalIgnoreCase) && (dName.Contains("Victor", StringComparison.OrdinalIgnoreCase) || dName.Contains("Gloria", StringComparison.OrdinalIgnoreCase) || dName.Contains("Marnie", StringComparison.OrdinalIgnoreCase) || dName.Contains("Hop", StringComparison.OrdinalIgnoreCase) || dName.Contains("Bede", StringComparison.OrdinalIgnoreCase) || dName.Contains("Leon", StringComparison.OrdinalIgnoreCase) || dName.Contains("Raihan", StringComparison.OrdinalIgnoreCase) || dName.Contains("Piers", StringComparison.OrdinalIgnoreCase) || dName.Contains("Nessa", StringComparison.OrdinalIgnoreCase) || dName.Contains("Bea", StringComparison.OrdinalIgnoreCase))) count++;
            else if (passiveName.Contains("Paldea", StringComparison.OrdinalIgnoreCase) && (dName.Contains("Florian", StringComparison.OrdinalIgnoreCase) || dName.Contains("Juliana", StringComparison.OrdinalIgnoreCase) || dName.Contains("Nemona", StringComparison.OrdinalIgnoreCase) || dName.Contains("Arven", StringComparison.OrdinalIgnoreCase) || dName.Contains("Penny", StringComparison.OrdinalIgnoreCase) || dName.Contains("Geeta", StringComparison.OrdinalIgnoreCase) || dName.Contains("Iono", StringComparison.OrdinalIgnoreCase) || dName.Contains("Grusha", StringComparison.OrdinalIgnoreCase))) count++;
            else if (other.Pair.Type == ActiveAttacker.Pair.Type) count++;
        }
        return Math.Clamp(count, 0, 2);
    }
}