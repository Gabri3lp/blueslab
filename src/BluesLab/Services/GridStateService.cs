using BluesLab.Models;

namespace BluesLab.Services;

public class GridStateService
{
    private static readonly int[][] HexDirections =
    [
        [1, 0, -1],
        [-1, 0, 1],
        [0, 1, -1],
        [0, -1, 1],
        [1, -1, 0],
        [-1, 1, 0]
    ];

    public HashSet<long> ActiveCells { get; } = new();
    public List<long> ActiveLearnMoveOrder { get; } = new();
    public bool HardCap { get; set; } = true;
    public int MaxEnergy { get; set; } = 60;

    public event Action? OnGridChanged;

    public void NotifyChanged() => OnGridChanged?.Invoke();

    public void ResetGrid(SyncPairDetail? pair, int moveLevel)
    {
        ActiveCells.Clear();
        ActiveLearnMoveOrder.Clear();
        if (pair != null && HardCap)
        {
            ActivateFreeCenterCells(pair, moveLevel);
        }
        NotifyChanged();
    }

    public int GetRemainingEnergy(SyncPairDetail? pair)
    {
        if (pair == null) return MaxEnergy;
        int used = pair.Grid
            .Where(c => ActiveCells.Contains(c.CellId))
            .Sum(c => c.EnergyCost);
        return MaxEnergy - used;
    }

    public int GetTotalOrbs(SyncPairDetail? pair)
    {
        if (pair == null) return 0;
        return pair.Grid
            .Where(c => ActiveCells.Contains(c.CellId))
            .Sum(c => c.OrbCost);
    }

    public bool HasSpecialOrbs(SyncPairDetail? pair)
    {
        return pair != null && pair.Grid.Any(c => c.Custom != null && c.Custom.Any(x => x > 0));
    }

    public int[] GetSpecialOrbsUsed(SyncPairDetail? pair)
    {
        var totals = new int[5];
        if (pair == null) return totals;

        foreach (var cell in pair.Grid)
        {
            if (ActiveCells.Contains(cell.CellId) && cell.Custom != null)
            {
                for (int i = 0; i < Math.Min(5, cell.Custom.Count); i++)
                {
                    totals[i] += cell.Custom[i];
                }
            }
        }
        return totals;
    }

    public bool IsAdjacentToCenter(GridCellItem cell)
    {
        foreach (var d in HexDirections)
        {
            if (cell.Q == d[0] && cell.R == d[1] && cell.S == d[2])
                return true;
        }
        return false;
    }

    public bool IsAdjacentToActiveOrCenter(GridCellItem cell, List<GridCellItem> allCells)
    {
        foreach (var d in HexDirections)
        {
            int nq = cell.Q + d[0];
            int nr = cell.R + d[1];
            int ns = cell.S + d[2];
            if (nq == 0 && nr == 0 && ns == 0) return true;

            foreach (var other in allCells)
            {
                if (other.Q == nq && other.R == nr && other.S == ns && ActiveCells.Contains(other.CellId))
                    return true;
            }
        }
        return false;
    }

    public void ActivateFreeCenterCells(SyncPairDetail pair, int moveLevel)
    {
        foreach (var cell in pair.Grid)
        {
            if (cell.EnergyCost == 0 && cell.MoveLevel <= Math.Clamp(moveLevel, 1, 5) && IsAdjacentToCenter(cell))
            {
                ActiveCells.Add(cell.CellId);
            }
        }
    }

    public void PruneDisconnected(List<GridCellItem> allCells)
    {
        var cellMap = allCells.ToDictionary(c => $"{c.Q},{c.R},{c.S}");
        var connected = new HashSet<long>();
        var queue = new Queue<(int Q, int R, int S)>();
        var visited = new HashSet<string> { "0,0,0" };
        queue.Enqueue((0, 0, 0));

        while (queue.Count > 0)
        {
            var pos = queue.Dequeue();
            foreach (var d in HexDirections)
            {
                int nq = pos.Q + d[0];
                int nr = pos.R + d[1];
                int ns = pos.S + d[2];
                string key = $"{nq},{nr},{ns}";
                if (visited.Contains(key)) continue;
                visited.Add(key);

                if (cellMap.TryGetValue(key, out var neighbor) && ActiveCells.Contains(neighbor.CellId))
                {
                    connected.Add(neighbor.CellId);
                    queue.Enqueue((nq, nr, ns));
                }
            }
        }

        ActiveCells.IntersectWith(connected);
        ActiveLearnMoveOrder.RemoveAll(id => !ActiveCells.Contains(id));
    }

    public void ToggleCell(SyncPairDetail pair, GridCellItem cell, int moveLevel)
    {
        if (ActiveCells.Contains(cell.CellId))
        {
            ActiveCells.Remove(cell.CellId);
            ActiveLearnMoveOrder.Remove(cell.CellId);
            if (HardCap)
            {
                PruneDisconnected(pair.Grid);
            }
        }
        else
        {
            if (cell.MoveLevel > Math.Clamp(moveLevel, 1, 5)) return;
            if (HardCap && !IsAdjacentToActiveOrCenter(cell, pair.Grid)) return;

            ActiveCells.Add(cell.CellId);
            if (cell.ColorKind == "learn" || cell.Title.StartsWith("Learn ", StringComparison.OrdinalIgnoreCase))
            {
                if (!ActiveLearnMoveOrder.Contains(cell.CellId))
                {
                    ActiveLearnMoveOrder.Add(cell.CellId);
                }
            }
        }

        NotifyChanged();
    }

    public List<MoveItem> GetLearnedMoves(SyncPairDetail? pair)
    {
        var moves = new List<MoveItem>();
        if (pair == null) return moves;

        foreach (var cellId in ActiveLearnMoveOrder.Take(3))
        {
            var cell = pair.Grid.FirstOrDefault(c => c.CellId == cellId);
            if (cell != null && !string.IsNullOrEmpty(cell.Title))
            {
                string moveName = cell.Title.Contains(":") ? cell.Title.Substring(0, cell.Title.IndexOf(":")).Trim() : cell.Title.Trim();
                if (moveName.StartsWith("Learn ", StringComparison.OrdinalIgnoreCase))
                {
                    moveName = moveName.Substring(6).Trim();
                }

                // Check if already in pair moves
                if (!pair.Moves.Any(m => string.Equals(m.Name, moveName, StringComparison.OrdinalIgnoreCase)))
                {
                    moves.Add(new MoveItem
                    {
                        Name = moveName,
                        Type = pair.Type,
                        Category = "Special",
                        Power = "100",
                        Accuracy = "100",
                        Gauge = "2",
                        Description = cell.Description,
                        IsSync = false
                    });
                }
            }
        }

        return moves;
    }

    public string ExportBuildToken(List<GridCellItem> grid)
    {
        var sorted = grid.OrderBy(c => c.CellId).ToList();
        int n = sorted.Count;
        byte[] bytes = new byte[(n + 7) / 8];
        for (int i = 0; i < n; i++)
        {
            if (ActiveCells.Contains(sorted[i].CellId))
            {
                bytes[i >> 3] |= (byte)(1 << (i & 7));
            }
        }
        return Convert.ToBase64String(bytes).Replace("+", "-").Replace("/", "_").TrimEnd('=');
    }

    public void ImportBuildToken(List<GridCellItem> grid, string token)
    {
        try
        {
            token = token.Trim();
            // Handle comma-separated cell IDs
            if (token.Contains(","))
            {
                var ids = token.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
                ActiveCells.Clear();
                foreach (var idStr in ids)
                {
                    if (long.TryParse(idStr, out long parsedId))
                    {
                        ActiveCells.Add(parsedId);
                    }
                }
                if (HardCap) PruneDisconnected(grid);
                NotifyChanged();
                return;
            }

            string b64 = token.Replace("-", "+").Replace("_", "/");
            switch (b64.Length % 4)
            {
                case 2: b64 += "=="; break;
                case 3: b64 += "="; break;
            }
            byte[] bytes = Convert.FromBase64String(b64);
            var sorted = grid.OrderBy(c => c.CellId).ToList();
            ActiveCells.Clear();
            for (int i = 0; i < sorted.Count && (i >> 3) < bytes.Length; i++)
            {
                int bit = (bytes[i >> 3] >> (i & 7)) & 1;
                if (bit == 1)
                {
                    ActiveCells.Add(sorted[i].CellId);
                }
            }
            if (HardCap)
            {
                PruneDisconnected(grid);
            }
            NotifyChanged();
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Failed to import build token: {ex.Message}");
        }
    }
}