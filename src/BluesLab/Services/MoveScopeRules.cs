namespace BluesLab.Services;

using BluesLab.Models;

/// <summary>
/// Centralized authority for move type applicability across all battle modifiers.
/// Directly mirrors the PoMaTools / PMEX calculation engine semantics:
/// - "MV": Regular Move (IsSync = false, IsMax = false)
/// - "SN": Sync Move (IsSync = true, IsMax = false)
/// - "MX": Max Move (IsSync = false, IsMax = true)
/// </summary>
public static class MoveScopeRules
{
    public enum MoveKind
    {
        RegularMove, // PoMaTools "MV"
        SyncMove,    // PoMaTools "SN"
        MaxMove      // PoMaTools "MX"
    }

    /// <summary>
    /// Classifies a move into its canonical PoMaTools kind: Regular ("MV"), Sync ("SN"), or Max ("MX").
    /// </summary>
    public static MoveKind GetMoveKind(MoveItem move)
    {
        if (move.IsMax) return MoveKind.MaxMove;
        if (move.IsSync) return MoveKind.SyncMove;
        return MoveKind.RegularMove;
    }

    /// <summary>
    /// Checks whether the move is a regular combat move ("MV").
    /// </summary>
    public static bool IsRegularMove(MoveItem move) => !move.IsSync && !move.IsMax;

    /// <summary>
    /// Checks whether the move is a Sync move ("SN").
    /// </summary>
    public static bool IsSyncMove(MoveItem move) => move.IsSync && !move.IsMax;

    /// <summary>
    /// Checks whether the move is a Dynamax / Gigantamax Max move ("MX").
    /// </summary>
    public static bool IsMaxMove(MoveItem move) => move.IsMax;

    /// <summary>
    /// Breaks on target (Physical / Special Break x1.5):
    /// PoMaTools: "MV" === z.kind && breaks
    /// Strictly applies ONLY to regular moves. Sync Moves and Max Moves are immune.
    /// </summary>
    public static bool AllowsBreaks(MoveItem move) => IsRegularMove(move);

    /// <summary>
    /// Damage Reduction screens on target (Reflect / Light Screen x0.66):
    /// Strictly applies ONLY to regular moves. Sync Moves and Max Moves ignore screens.
    /// Critical hits also bypass screens regardless of move type.
    /// </summary>
    public static bool AllowsScreens(MoveItem move) => IsRegularMove(move);

    /// <summary>
    /// Multi-target AoE damage reduction (3 targets = x0.5, 2 targets = x0.66):
    /// PoMaTools: field.targets > 1 && "SN" !== z.kind && "MX" !== z.kind
    /// Strictly applies ONLY to regular multi-target moves without inherent decay protection.
    /// </summary>
    public static bool AllowsAoEPenalty(MoveItem move) => IsRegularMove(move);

    /// <summary>
    /// Regional Circles (+10% to +40% depending on region and ally count):
    /// PoMaTools: "MV" === z.kind || "SN" == z.kind
    /// Applies to regular moves and sync moves. Max Moves do NOT receive Regional Circle boosts.
    /// </summary>
    public static bool AllowsCircles(MoveItem move) => !move.IsMax;

    /// <summary>
    /// Master Passives (e.g. Master Flagbearer, Master Pride, etc.):
    /// PoMaTools: "MX" !== z.kind
    /// Applies to regular moves and sync moves. Max Moves do NOT receive Master Passive bonuses.
    /// </summary>
    public static bool AllowsMasterPassives(MoveItem move) => !move.IsMax;

    /// <summary>
    /// Physical / Special Move Boost Next (PMUN / SMUN: +40% per stack):
    /// PoMaTools: "MV" === z.kind
    /// Applies ONLY to regular moves.
    /// </summary>
    public static bool AllowsMoveBoostNext(MoveItem move) => IsRegularMove(move);

    /// <summary>
    /// Sync Move Boost Next (SYUN: +10% per stack):
    /// PoMaTools: "SN" === z.kind
    /// Applies ONLY to sync moves.
    /// </summary>
    public static bool AllowsSyncBoostNext(MoveItem move) => move.IsSync;

    /// <summary>
    /// Terastal Move Boost (x1.5 matching type, x2.0 Stellar):
    /// Applies only to regular moves.
    /// </summary>
    public static bool AllowsTeraBoost(MoveItem move) => IsRegularMove(move);

    /// <summary>
    /// Checks whether a passive or grid skill target scope applies to the given move.
    /// </summary>
    public static bool AllowsPassive(string? appliesTo, MoveItem move)
    {
        if (string.IsNullOrWhiteSpace(appliesTo) || appliesTo.Equals("all", StringComparison.OrdinalIgnoreCase))
            return true;

        string target = appliesTo.ToLowerInvariant().Trim();
        if (target == "sync_move")
            return move.IsSync;
        if (target is "moves" or "pokemon_moves" or "p_moves")
            return IsRegularMove(move);
        if (target == "max_move")
            return move.IsMax;
        if (target == "moves_and_sync")
            return !move.IsMax;

        return true;
    }
}
