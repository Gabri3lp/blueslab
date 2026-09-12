using System.Text.RegularExpressions;
using BluesLab.Models;

namespace BluesLab.Services;

public readonly struct FormattedTileLine
{
    public string Text { get; }
    public double YOffset { get; }

    public FormattedTileLine(string text, double yOffset)
    {
        Text = text;
        YOffset = yOffset;
    }
}

public class FormattedTileLabel
{
    public List<FormattedTileLine> Lines { get; }
    public double FontSize { get; }

    public FormattedTileLabel(List<FormattedTileLine> lines, double fontSize)
    {
        Lines = lines;
        FontSize = fontSize;
    }
}

public static class GridTileFormatter
{
    private static readonly Regex EsStatRegex = new(@"^(PS|Ataque|Defensa|At\.\s*Esp\.|Def\.\s*Esp\.|Velocidad)\s*\+\s*(\d+)$", RegexOptions.IgnoreCase | RegexOptions.Compiled);
    private static readonly Regex EnStatRegex = new(@"^(HP|Attack|Defense|Sp\.\s*Atk|Sp\.\s*Def|Speed)\s*\+\s*(\d+)$", RegexOptions.IgnoreCase | RegexOptions.Compiled);
    private static readonly Regex NumberOnlyRegex = new(@"\+\s*(\d+)", RegexOptions.Compiled);
    private static readonly Regex MovePowerRegex = new(@"^(.*?):\s*(?:Power|Potencia)\s*\+\s*(\d+)$", RegexOptions.IgnoreCase | RegexOptions.Compiled);
    private static readonly Regex MoveMgrRegex = new(@"^(.*?):\s*(?:Move Gauge Refresh|Movimiento Llenabarras|Llenabarras)\s*\+?(\d+)$", RegexOptions.IgnoreCase | RegexOptions.Compiled);
    private static readonly Regex MoveMprRegex = new(@"^(.*?):\s*(?:MP Refresh|Recupera PM|Movimiento Recupera PM)\s*\+?(\d+)$", RegexOptions.IgnoreCase | RegexOptions.Compiled);
    private static readonly Regex MoveAccRegex = new(@"^(.*?):\s*(?:Accuracy|Precisión)\s*\+\s*(\d+)$", RegexOptions.IgnoreCase | RegexOptions.Compiled);
    private static readonly Regex MoveHealerRegex = new(@"^(.*?):\s*(?:Master Healer|Efecto Curativo)\s*\+?(\d+)$", RegexOptions.IgnoreCase | RegexOptions.Compiled);
    private static readonly Regex LearnMoveRegex = new(@"^(?:Learn Move|Aprender mov\.)(?::\s*|\s+)(.*)$", RegexOptions.IgnoreCase | RegexOptions.Compiled);

    private static readonly Dictionary<string, string> MoveShortcuts = new(StringComparer.OrdinalIgnoreCase)
    {
        ["Thunderbolt"] = "T-Bolt",
        ["Hydro Pump"] = "H-Pump",
        ["Hidrobomba"] = "H-Bomba",
        ["Earthquake"] = "EQ",
        ["Terremoto"] = "Terrem.",
        ["Hyper Beam"] = "H-Beam",
        ["Hiperrayo"] = "H-Rayo",
        ["Solar Beam"] = "SolarBeam",
        ["Rayo Solar"] = "R.Solar",
        ["Fire Blast"] = "FireBlast",
        ["Llamarada"] = "Llamar.",
        ["Potion"] = "Potion",
        ["Poción"] = "Poción",
        ["Swords Dance"] = "SwordsDance",
        ["Danza Espada"] = "D.Espada",
        ["Shadow Ball"] = "Shd Ball",
        ["Bola Sombra"] = "B.Sombra",
        ["Focus Blast"] = "FocusBlast",
        ["Onda Certera"] = "O.Certera",
        ["Flamethrower"] = "Flamethr.",
        ["Lanzallamas"] = "Lanzall.",
        ["B Volt Tackle"] = "B V.Tackle",
        ["Volt Tackle"] = "V.Tackle",
        ["Placaje Eléc."] = "Plac.Eléc.",
        ["Ice Beam"] = "Ice Beam",
        ["Rayo Hielo"] = "R.Hielo",
        ["Psychic"] = "Psychic",
        ["Psíquico"] = "Psíquico",
        ["Energy Ball"] = "EnergyBall",
        ["Energibola"] = "Energibola",
        ["Stone Edge"] = "Stone Edge",
        ["Roca Afilada"] = "R.Afilada",
        ["Drain Punch"] = "DrainPunch",
        ["Puño Drenaje"] = "P.Drenaje",
        ["Giga Drain"] = "Giga Drain",
        ["Gigadrenado"] = "Gigadren."
    };

    private static readonly (string Pattern, string Replacement)[] EsReplacements =
    [
        (@"Inmunidad Golpes Críticos", "Vigilancia"),
        (@"Inmunidad Reducción Defensa", "Inm. Def ↓"),
        (@"Inmunidad Reducción Ataque", "Inm. Atq ↓"),
        (@"Inmunidad Reducción Velocidad", "Inm. Vel ↓"),
        (@"Inmunidad Reducción Def\. Esp\.", "Inm. DefEsp↓"),
        (@"Inmunidad Reducción At\. Esp\.", "Inm. AtqEsp↓"),
        (@"Inmunidad Retroceso", "Inm. Retro."),
        (@"Curación Problemas Estado", "Cura Estado"),
        (@"Inmunidad Problemas Estado", "Inm. Estado"),
        (@"Primeros Auxilios (\d+)", "1.os Aux $1"),
        (@"Regeneración Saludable", "Regen. Salud."),
        (@"Entrada Furor (\d+)", "Ent. Furor $1"),
        (@"Protección Arena", "Prot. Arena"),
        (@"Movimiento Aliado Curación.*", "Curac. Aliado"),
        (@"Aceleración Mov\. Compi", "Acel. Compi"),
        (@"Llenabarras en 1\.er Apuro (\d+)", "Apuro MGR $1"),
        (@"Daño Llenabarras (\d+)", "Daño MGR $1"),
        (@"Acierto Llenabarras (\d+)", "Acierto MGR $1")
    ];

    private static readonly (string Pattern, string Replacement)[] EnReplacements =
    [
        (@"Critical Strike (\d+)", "Crit Strike $1"),
        (@"Hostile Environment (\d+)", "Hostile Env $1"),
        (@"Bob and Weave", "Bob & Weave"),
        (@"Healthy Healing", "Healthy Heal"),
        (@"Natural Remedy", "Nat. Remedy"),
        (@"Quick Cure", "Quick Cure"),
        (@"Sand Shelter", "Sand Shelter"),
        (@"First Aid (\d+)", "First Aid $1")
    ];

    public static FormattedTileLabel FormatTile(string? rawTitle, long abilityId, string language)
    {
        if (string.IsNullOrWhiteSpace(rawTitle))
        {
            return new FormattedTileLabel(new List<FormattedTileLine>(), 8.0);
        }

        var t = rawTitle.Replace("\r", "").Replace("\n", " ").Trim();
        t = Regex.Replace(t, @"\[[^\]]+\]", "").Trim();
        while (t.Contains("  ")) t = t.Replace("  ", " ");

        var isEs = string.Equals(language, "es", StringComparison.OrdinalIgnoreCase);

        // 1. Stats
        var mEs = EsStatRegex.Match(t);
        if (mEs.Success)
        {
            var stat = mEs.Groups[1].Value;
            var val = mEs.Groups[2].Value;
            var shortStat = stat.ToLowerInvariant() switch
            {
                "ps" => "PS",
                "ataque" => "Atq",
                "defensa" => "Def",
                "at. esp." => "At.Esp",
                "def. esp." => "Def.Esp",
                "velocidad" => "Vel",
                _ => stat
            };
            return BuildLabel([$"{shortStat} +{val}"]);
        }

        var mEn = EnStatRegex.Match(t);
        if (mEn.Success)
        {
            var stat = mEn.Groups[1].Value;
            var val = mEn.Groups[2].Value;
            var shortStat = stat.ToLowerInvariant() switch
            {
                "hp" => "HP",
                "attack" => "Atk",
                "defense" => "Def",
                "sp. atk" => "SpA",
                "sp. def" => "SpD",
                "speed" => "Spe",
                _ => stat
            };
            return BuildLabel([$"{shortStat} +{val}"]);
        }

        // 2. Sync Moves
        if (t.Contains("Sync Move", StringComparison.OrdinalIgnoreCase) ||
            t.Contains("Movimiento Compi", StringComparison.OrdinalIgnoreCase) ||
            t.Contains("Impact: Power", StringComparison.OrdinalIgnoreCase) ||
            t.Contains("Impacto: Potencia", StringComparison.OrdinalIgnoreCase) ||
            t.Contains("Beam: Power", StringComparison.OrdinalIgnoreCase))
        {
            var mNum = NumberOnlyRegex.Match(t);
            var val = mNum.Success ? mNum.Groups[1].Value : "";
            var syncText = isEs ? "Compi" : "Sync";
            var pwrText = !string.IsNullOrEmpty(val) ? $"+{val}" : "+Power";
            return BuildLabel([syncText, pwrText]);
        }

        // 3. Max / Dynamax Moves
        if (t.Contains("Max Move", StringComparison.OrdinalIgnoreCase) ||
            t.Contains("Movimiento Dynamax", StringComparison.OrdinalIgnoreCase))
        {
            var mNum = NumberOnlyRegex.Match(t);
            var val = mNum.Success ? mNum.Groups[1].Value : "";
            var maxText = isEs ? "Dyna" : "Max";
            var pwrText = !string.IsNullOrEmpty(val) ? $"+{val}" : "+Power";
            return BuildLabel([maxText, pwrText]);
        }

        // 4. Move Power Ups
        var mPwr = MovePowerRegex.Match(t);
        if (mPwr.Success)
        {
            var move = ShortenMove(mPwr.Groups[1].Value);
            return BuildLabel([move, $"+{mPwr.Groups[2].Value}"]);
        }

        // 5. Move Gauge Refresh
        var mMgr = MoveMgrRegex.Match(t);
        if (mMgr.Success)
        {
            var move = ShortenMove(mMgr.Groups[1].Value);
            return BuildLabel([move, $"MGR {mMgr.Groups[2].Value}"]);
        }

        // 6. MP Refresh
        var mMpr = MoveMprRegex.Match(t);
        if (mMpr.Success)
        {
            var move = ShortenMove(mMpr.Groups[1].Value);
            return BuildLabel([move, $"MPR {mMpr.Groups[2].Value}"]);
        }

        // 7. Accuracy
        var mAcc = MoveAccRegex.Match(t);
        if (mAcc.Success)
        {
            var move = ShortenMove(mAcc.Groups[1].Value);
            var prefix = isEs ? "Prec" : "Acc";
            return BuildLabel([move, $"{prefix} +{mAcc.Groups[2].Value}"]);
        }

        // 8. Master Healer
        var mHeal = MoveHealerRegex.Match(t);
        if (mHeal.Success)
        {
            var move = ShortenMove(mHeal.Groups[1].Value);
            var healText = isEs ? $"Curativo {mHeal.Groups[2].Value}" : $"Healer {mHeal.Groups[2].Value}";
            return BuildLabel([move, healText]);
        }

        // 9. Learn move
        var mLrn = LearnMoveRegex.Match(t);
        if (mLrn.Success)
        {
            var learnText = isEs ? "Aprender" : "Learn";
            var move = ShortenMove(mLrn.Groups[1].Value);
            return BuildLabel([learnText, move]);
        }

        // 10. Specific Language Passive Replacements
        if (isEs)
        {
            foreach (var (pattern, replacement) in EsReplacements)
            {
                if (Regex.IsMatch(t, pattern, RegexOptions.IgnoreCase))
                {
                    t = Regex.Replace(t, pattern, replacement, RegexOptions.IgnoreCase);
                    break;
                }
            }
        }
        else
        {
            foreach (var (pattern, replacement) in EnReplacements)
            {
                if (Regex.IsMatch(t, pattern, RegexOptions.IgnoreCase))
                {
                    t = Regex.Replace(t, pattern, replacement, RegexOptions.IgnoreCase);
                    break;
                }
            }
        }

        // Fits nicely on 1 line
        if (t.Length <= 10)
        {
            return BuildLabel([t]);
        }

        // Colon-based splitting
        if (t.Contains(": "))
        {
            var colonParts = t.Split(new[] { ": " }, 2, StringSplitOptions.RemoveEmptyEntries);
            if (colonParts.Length == 2)
            {
                var p1 = ShortenMove(colonParts[0]);
                var p2 = colonParts[1].Trim();
                if (p2.Length > 11)
                {
                    var p2Words = p2.Split(' ', StringSplitOptions.RemoveEmptyEntries);
                    if (p2Words.Length == 2 && p2Words[0].Length <= 8)
                    {
                        return BuildLabel([p1, p2Words[0], p2Words[1]]);
                    }
                    p2 = p2.Substring(0, 10) + ".";
                }
                return BuildLabel([p1, p2]);
            }
        }

        // Multi-word wrapping into 2 lines
        var words = t.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        if (words.Length == 2)
        {
            var w1 = words[0].Length > 11 ? words[0].Substring(0, 10) + "." : words[0];
            var w2 = words[1].Length > 11 ? words[1].Substring(0, 10) + "." : words[1];
            return BuildLabel([w1, w2]);
        }

        if (words.Length >= 3)
        {
            if (words[0].Length + words[1].Length + 1 <= 11)
            {
                var l1 = words[0] + " " + words[1];
                var rest = string.Join(" ", words.Skip(2));
                if (rest.Length > 11) rest = rest.Substring(0, 10) + ".";
                return BuildLabel([l1, rest]);
            }
            if (words.Length == 3 && words[1].Length + words[2].Length + 1 <= 11)
            {
                var w1 = words[0].Length > 11 ? words[0].Substring(0, 10) + "." : words[0];
                return BuildLabel([w1, words[1] + " " + words[2]]);
            }
            {
                var w1 = words[0].Length > 11 ? words[0].Substring(0, 10) + "." : words[0];
                var w2 = words[1].Length > 11 ? words[1].Substring(0, 10) + "." : words[1];
                return BuildLabel([w1, w2]);
            }
        }

        // Single long word
        return BuildLabel([t.Substring(0, Math.Min(10, t.Length)) + "."]);
    }

    private static string ShortenMove(string name)
    {
        name = name.Trim();
        if (MoveShortcuts.TryGetValue(name, out var shortcut))
        {
            return shortcut;
        }

        if (name.Length > 10)
        {
            return name.Substring(0, 9) + ".";
        }

        return name;
    }

    private static FormattedTileLabel BuildLabel(IReadOnlyList<string> rawLines)
    {
        var validLines = rawLines.Where(l => !string.IsNullOrWhiteSpace(l)).Select(l => l.Trim()).ToList();
        if (validLines.Count == 0)
        {
            return new FormattedTileLabel(new List<FormattedTileLine>(), 8.0);
        }

        if (validLines.Count == 1)
        {
            var len = validLines[0].Length;
            var fontSize = len switch
            {
                <= 6 => 8.8,
                <= 9 => 8.2,
                _ => 7.5
            };
            return new FormattedTileLabel(
            [
                new FormattedTileLine(validLines[0], 0.0)
            ], fontSize);
        }

        if (validLines.Count == 2)
        {
            var maxLen = Math.Max(validLines[0].Length, validLines[1].Length);
            var fontSize = maxLen switch
            {
                <= 6 => 8.2,
                <= 9 => 7.7,
                _ => 7.0
            };
            return new FormattedTileLabel(
            [
                new FormattedTileLine(validLines[0], -5.2),
                new FormattedTileLine(validLines[1], 5.8)
            ], fontSize);
        }

        // 3 lines
        return new FormattedTileLabel(
        [
            new FormattedTileLine(validLines[0], -9.5),
            new FormattedTileLine(validLines[1], 0.0),
            new FormattedTileLine(validLines[2], 9.5)
        ], 6.5);
    }

    public static string GetTileLabelSvg(string? rawTitle, long abilityId, string language, double cx, double cy, bool isLocked, bool isActive)
    {
        var label = FormatTile(rawTitle, abilityId, language);
        if (label.Lines.Count == 0) return string.Empty;

        var lockClass = isLocked ? " text-locked" : "";
        var activeClass = isActive ? " text-active" : "";
        var fs = label.FontSize.ToString("0.#", System.Globalization.CultureInfo.InvariantCulture);
        var cxStr = cx.ToString("0.#", System.Globalization.CultureInfo.InvariantCulture);
        var cyStr = cy.ToString("0.#", System.Globalization.CultureInfo.InvariantCulture);

        var sb = new System.Text.StringBuilder();
        sb.Append($"<text x=\"{cxStr}\" y=\"{cyStr}\" text-anchor=\"middle\" dominant-baseline=\"central\" class=\"hex-tile-label{lockClass}{activeClass}\" font-size=\"{fs}\" style=\"pointer-events: none; user-select: none;\">");
        foreach (var line in label.Lines)
        {
            var yStr = (cy + line.YOffset).ToString("0.#", System.Globalization.CultureInfo.InvariantCulture);
            var encodedText = System.Net.WebUtility.HtmlEncode(line.Text);
            sb.Append($"<tspan x=\"{cxStr}\" y=\"{yStr}\">{encodedText}</tspan>");
        }
        sb.Append("</text>");
        return sb.ToString();
    }
}
