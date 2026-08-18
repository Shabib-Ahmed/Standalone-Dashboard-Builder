from __future__ import annotations

import json
from abc import ABC
from dataclasses import dataclass, field
from typing import Any, Union


# ---------------------------------------------------------------------------
# Data-model types
# ---------------------------------------------------------------------------

@dataclass
class Tab:
    key: str
    label: str
    content_html: str


@dataclass
class Section:
    key: str
    label: str
    date_range: tuple[str, str] | None = None
    tabs: list[Tab] = field(default_factory=list)

    @property
    def heading(self) -> str:
        if self.date_range:
            return f"{self.label} ({self.date_range[0]} to {self.date_range[1]})"
        return self.label

    def add_tab(self, key: str, label: str, content_html: str) -> "Section":
        self.tabs.append(Tab(key, label, content_html))
        return self

@dataclass
class GraphRow:
    graphs: list[GraphConfig]
    layout: str = "stack"      # "stack" | "halves" | "thirds" | "sidebar-left" | "sidebar-right"
    gap: int = 16              # px gap between columns


# ---------------------------------------------------------------------------
# Control configs
# ---------------------------------------------------------------------------

@dataclass
class DropdownControl:
    """A <select> rendered above charts in a view."""
    control_id: str
    label: str
    options: list[str]
    on_change: str = ""


@dataclass
class RangeInputControl:
    """Two numeric <input> fields (lo / hi) for workload-range filtering."""
    lo_id: str
    hi_id: str
    label: str = "Workload range"
    result_div_id: str = "range-result"


ControlConfig = Union[DropdownControl, RangeInputControl]


# ---------------------------------------------------------------------------
# Graph option types
# ---------------------------------------------------------------------------

class GraphOptions(ABC):
    """Abstract base — never instantiated directly."""


@dataclass
class LineOptions(GraphOptions):
    """One or more series plotted as lines against a shared x-axis."""
    series: list[dict[str, str]] = field(default_factory=list)
    x_col: str = ""
    x_label: str = ""
    y_label: str = ""
    title: str = ""
    connect_gaps: bool = False


@dataclass
class BarOptions(GraphOptions):
    series: list[dict[str, str]] = field(default_factory=list)
    x_col: str = ""
    x_label: str = ""
    y_label: str = ""
    title: str = ""
    barmode: str = "group"  # "group" | "stack" | "overlay"


@dataclass
class DualAxisOptions(GraphOptions):
    """Left-axis series vs right-axis series, with optional overlay chart."""
    x_col: str = ""
    x_label: str = ""
    left_col: str = ""
    left_label: str = ""
    right_col: str = ""
    right_label: str = ""
    title: str = ""
    show_overlay_chart: bool = False


@dataclass
class RangeFilterOptions:
    """
    Workload-range filter panel rendered beneath a ScatterOptions chart.
    Recalculates Pearson r/p on the filtered subset inline.
    """
    result_div_id: str = "corr-range-result"
    lo_input_id: str = "corr-range-lo"
    hi_input_id: str = "corr-range-hi"


@dataclass
class ScatterOptions(GraphOptions):
    x_col: str = ""
    x_label: str = ""
    y_col: str = ""
    y_label: str = ""
    id_col: str = ""
    time_col: str = ""
    title: str = ""
    show_regression: bool = True
    show_loess: bool = True
    show_stats_badge: bool = True
    weight_col: str = ""          
    range_filter: RangeFilterOptions | None = None


@dataclass
class TableOptions(GraphOptions):
    """Renders a plain HTML table from the view data."""
    columns: list[dict[str, str]] = field(default_factory=list)
    time_col: str = ""
    time_label: str = ""


@dataclass
class ComparisonOptions(GraphOptions):
    """
    Side-by-side comparison of two groups across time buckets,
    including a stats table with 95% CI.
    """
    groups: list[str] = field(default_factory=list)
    group_label: str = "Group"
    filter_keys: list[str] = field(default_factory=list)
    filter_label: str = "Filter"
    default_filter: str = ""
    bucket_label: str = "Bucket"
    value_label: str = "Value"
    # Pre-serialised JSON: filter → group → list[{bucket, mean, std, n, ci}]
    data_json: str = "null"
    t_crit_json: str = "{}"


# ---------------------------------------------------------------------------
# Graph / view container types
# ---------------------------------------------------------------------------

@dataclass
class GraphConfig:
    div_id: str
    options: GraphOptions
    height: int = 500  # pixels; ignored for TableOptions


@dataclass
class ViewConfig:
    key: str
    tab_label: str
    heading: str
    description: str = ""
    data_json: str = "null"
    controls: list[ControlConfig] = field(default_factory=list)
    rows: list[GraphRow] = field(default_factory=list)

# ---------------------------------------------------------------------------
# HTMLBuilder
# ---------------------------------------------------------------------------

class HTMLBuilder:
    def __init__(
        self,
        title: str,
        main_tab_label: str,
        dropdown_label: str,
        plotly_version: str,
        template: str,
    ) -> None:
        self.title = title
        self.main_tab_label = main_tab_label
        self.dropdown_label = dropdown_label
        self.plotly_version = plotly_version
        self.template = template
        self.sections: list[Section] = []
        self.views: list[ViewConfig] = []

    # ------------------------------------------------------------------
    # Builder methods
    # ------------------------------------------------------------------

    def add_section(
        self,
        key: str,
        label: str,
        date_range: tuple[str, str] | None = None,
    ) -> Section:
        sec = Section(key=key, label=label, date_range=date_range)
        self.sections.append(sec)
        return sec

    def add_button(
        self,
        section_key: str,
        tab_key: str,
        button_label: str,
        content_html: str,
    ) -> "HTMLBuilder":
        """Append a toggle button fragment to an existing tab's content."""
        toggle_fragment = (
            f'<div class="tab-toggle" data-label="{button_label}" '
            f'style="display:none;">{content_html}</div>'
        )
        tab = self._find_tab(section_key, tab_key)
        tab.content_html += toggle_fragment
        return self

    def add_dropdown(
        self,
        section_key: str,
        tab_key: str,
        dropdown_id: str,
        label: str,
        options: list[str],
        on_change_js: str = "",
    ) -> "HTMLBuilder":
        """Prepend a <select> dropdown to an existing tab's content."""
        opts_html = "\n".join(f'<option value="{o}">{o}</option>' for o in options)
        onchange_attr = f' onchange="{on_change_js}()"' if on_change_js else ""
        select_html = (
            f'<div style="margin-bottom:12px;">'
            f'<label><strong>{label}:</strong></label>'
            f'<select id="{dropdown_id}"{onchange_attr} style="padding:6px;margin-left:8px;">'
            f"{opts_html}</select></div>"
        )
        tab = self._find_tab(section_key, tab_key)
        tab.content_html = select_html + tab.content_html
        return self

    def add_view(self, view: ViewConfig) -> "HTMLBuilder":
        self.views.append(view)
        return self

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def render(self) -> str:
        """Render the full HTML string."""
        replacements = {
            "%%PLOTLY_VERSION%%": self.plotly_version,
            "%%TITLE%%": self.title,
            "%%MAIN_TAB_LABEL%%": self.main_tab_label,
            "%%DROPDOWN_LABEL%%": self.dropdown_label,
            "%%SECTION_DROPDOWN%%": self._section_dropdown_html(),
            "%%SECTIONS%%": self._sections_html(),
            "%%VIEW_TAB_BUTTONS%%": self._view_tab_buttons_html(),
            "%%VIEWS%%": self._views_html(),
            "%%VIEW_JS%%": self._view_js(),
        }
        html = self.template
        for marker, value in replacements.items():
            html = html.replace(marker, value)
        return html

    def save(self, path: str) -> None:
        from pathlib import Path
        Path(path).write_text(self.render(), encoding="utf-8")

    # ------------------------------------------------------------------
    # Private helpers — lookup
    # ------------------------------------------------------------------

    def _find_tab(self, section_key: str, tab_key: str) -> Tab:
        for sec in self.sections:
            if sec.key == section_key:
                for tab in sec.tabs:
                    if tab.key == tab_key:
                        return tab
                raise KeyError(f"No tab {tab_key!r} in section {section_key!r}.")
        raise KeyError(f"No section {section_key!r}.")

    # ------------------------------------------------------------------
    # Private helpers — HTML generation
    # ------------------------------------------------------------------

    def _section_dropdown_html(self) -> str:
        return "\n".join(
            f'<option value="{s.key}">{s.label}</option>'
            for s in self.sections
        )

    def _sections_html(self) -> str:
        parts: list[str] = []
        for i, sec in enumerate(self.sections):
            display = "block" if i == 0 else "none"
            tab_keys_literal = "[" + ",".join(f"'{t.key}'" for t in sec.tabs) + "]"

            buttons = "\n".join(
                f'<button onclick="showTab(this,\'{sec.key}\',\'{t.key}\',{tab_keys_literal})"'
                f'{" class=\"active-tab\"" if j == 0 else ""}>'
                f"{t.label}</button>"
                for j, t in enumerate(sec.tabs)
            )
            tab_divs = "\n".join(
                f'<div id="{sec.key}_{t.key}" class="tab-content"'
                f' style="display:{"block" if j == 0 else "none"};">'
                f"{t.content_html}</div>"
                for j, t in enumerate(sec.tabs)
            )
            parts.append(
                f'<div class="section-panel" id="{sec.key}" style="display:{display};">'
                f"<h2>{sec.heading}</h2>"
                f'<div class="tabs">{buttons}</div>'
                f"{tab_divs}</div>"
            )
        return "\n".join(parts)

    def _view_tab_buttons_html(self) -> str:
        return "\n".join(
            f'<button id="btn-{v.key}" onclick="switchView(\'{v.key}\')">'
            f"{v.tab_label}</button>"
            for v in self.views
        )

    def _views_html(self) -> str:
        return "\n".join(self._render_view(v) for v in self.views)

    def _render_view(self, v: ViewConfig) -> str:
        controls_html = "\n".join(self._render_control(c, v.key) for c in v.controls)
        desc_html = (
            f'<p style="margin:0 0 12px;color:#555;">{v.description}</p>'
            if v.description else ""
        )

        LAYOUT_WIDTHS = {
            "stack":         ["100%"],
            "halves":        ["50%", "50%"],
            "thirds":        ["33.33%", "33.33%", "33.33%"],
            "sidebar-left":  ["30%", "70%"],
            "sidebar-right": ["70%", "30%"],
        }

        rows_html = []
        for row in v.rows:
            widths = LAYOUT_WIDTHS.get(row.layout, ["100%"])
            if row.layout == "stack" or len(row.graphs) == 1:
                rows_html.append(self._render_graph(row.graphs[0], v.key))
            else:
                cols = []
                for i, g in enumerate(row.graphs):
                    w = widths[i] if i < len(widths) else "auto"
                    inner = self._render_graph(g, v.key)
                    cols.append(
                        f'<div style="flex:0 0 {w};min-width:0;">{inner}</div>'
                    )
                rows_html.append(
                    f'<div style="display:flex;gap:{row.gap}px;margin-top:20px;">'
                    + "".join(cols)
                    + '</div>'
                )

        return (
            f'<div id="view-{v.key}" style="display:none;">\n'
            f'  <h2 style="margin:18px 0 8px;">{v.heading}</h2>\n'
            f"  {desc_html}\n"
            f'  <div class="view-controls" style="margin-bottom:15px;">\n'
            f"    {controls_html}\n"
            f"  </div>\n"
            + "\n".join(rows_html)
            + "\n</div>\n"
        )

    def _render_control(self, c: ControlConfig, view_key: str) -> str:
        if isinstance(c, DropdownControl):
            opts_html = "\n".join(
                f'<option value="{o}">{o}</option>' for o in c.options
            )
            on_change = c.on_change or f"updateView('{view_key}')"
            return (
                f'<div style="display:inline-block;margin-right:20px;">'
                f'<label><strong>{c.label}:&nbsp;</strong></label>'
                f'<select id="{c.control_id}" onchange="{on_change}"'
                f' style="padding:8px;">'
                f"{opts_html}</select></div>"
            )
        if isinstance(c, RangeInputControl):
            return (
                f'<div style="display:flex;flex-wrap:wrap;gap:16px;align-items:center;'
                f'margin-bottom:12px;">'
                f'<span style="font-weight:600;">{c.label}:</span>'
                f'<label>From&nbsp;<input id="{c.lo_id}" type="number" step="0.01"'
                f' style="width:90px;padding:4px 6px;font-size:14px;"></label>'
                f'<label>To&nbsp;<input id="{c.hi_id}" type="number" step="0.01"'
                f' style="width:90px;padding:4px 6px;font-size:14px;"></label>'
                f'</div>'
                f'<div id="{c.result_div_id}"'
                f' style="font-size:15px;line-height:1.8;font-family:monospace;"></div>'
            )
        raise TypeError(f"Unknown ControlConfig type: {type(c)}")

    def _render_graph(self, g: GraphConfig, view_key: str = "") -> str:
        o = g.options
        if isinstance(o, (LineOptions, BarOptions, DualAxisOptions, ScatterOptions)):
            html = (
                f'<div id="{g.div_id}"'
                f' style="margin-top:20px;height:{g.height}px;"></div>\n'
            )
            if isinstance(o, DualAxisOptions) and o.show_overlay_chart:
                html += (
                    f'<div id="{g.div_id}-overlay"'
                    f' style="margin-top:30px;height:{g.height}px;"></div>\n'
                )
            if isinstance(o, ScatterOptions) and o.range_filter:
                html += self._render_range_filter_panel(o.range_filter)
            return html

        if isinstance(o, TableOptions):
            return f'<div id="{g.div_id}" style="margin-top:20px;overflow-x:auto;"></div>\n'

        if isinstance(o, ComparisonOptions):
            return self._render_comparison_div(g, view_key)

        raise TypeError(f"Unknown GraphOptions type: {type(o)}")

    def _render_range_filter_panel(self, rf: RangeFilterOptions) -> str:
        return (
            f'<div style="margin-top:24px;padding:16px 20px;background:#f8f9fa;'
            f'border:1px solid #dee2e6;border-radius:8px;">\n'
            f'  <div style="display:flex;flex-wrap:wrap;gap:16px;align-items:center;'
            f'margin-bottom:12px;">\n'
            f'    <span style="font-weight:600;">Workload range:</span>\n'
            f'    <label>From&nbsp;<input id="{rf.lo_input_id}" type="number" step="0.01"'
            f' style="width:90px;padding:4px 6px;font-size:14px;"></label>\n'
            f'    <label>To&nbsp;<input id="{rf.hi_input_id}" type="number" step="0.01"'
            f' style="width:90px;padding:4px 6px;font-size:14px;"></label>\n'
            f'  </div>\n'
            f'  <div id="{rf.result_div_id}"'
            f' style="font-size:15px;line-height:1.8;font-family:monospace;"></div>\n'
            f'</div>\n'
        )

    def _render_comparison_div(self, g: GraphConfig, view_key: str) -> str:
        o: ComparisonOptions = g.options  # type: ignore[assignment]
        group_opts = "\n".join(
            f'<option value="{grp}">{grp}</option>' for grp in o.groups
        )
        filter_opts = "\n".join(
            f'<option value="{k}"{" selected" if k == o.default_filter else ""}>'
            f"{k}</option>"
            for k in o.filter_keys
        )
        update_call = f"updateView('{view_key}')"
        return (
            f'<div id="{g.div_id}-selectors" style="margin-bottom:15px;">\n'
            f'  <label><strong>{o.group_label} 1:</strong></label>\n'
            f'  <select id="{g.div_id}-unit1" onchange="{update_call}"'
            f' style="padding:8px;margin-right:20px;">\n'
            f'    <option value="">-- Select --</option>{group_opts}\n'
            f'  </select>\n'
            f'  <label><strong>{o.group_label} 2:</strong></label>\n'
            f'  <select id="{g.div_id}-unit2" onchange="{update_call}"'
            f' style="padding:8px;margin-right:20px;">\n'
            f'    <option value="">-- Select --</option>{group_opts}\n'
            f'  </select>\n'
            f'  <label><strong>{o.filter_label}:</strong></label>\n'
            f'  <select id="{g.div_id}-filter" onchange="{update_call}"'
            f' style="padding:8px;">{filter_opts}</select>\n'
            f'</div>\n'
            f'<div id="{g.div_id}-chart" style="margin-top:20px;"></div>\n'
            f'<div id="{g.div_id}-table" style="margin-top:20px;overflow-x:auto;"></div>\n'
        )

    # ------------------------------------------------------------------
    # Private helpers — JavaScript generation
    # ------------------------------------------------------------------

    def _view_js(self) -> str:
        blocks = [self._js_shared_utils()]
        for v in self.views:
            blocks.append(self._js_for_view(v))
        blocks.append(self._js_dispatcher())
        return "<script>\n" + "\n".join(blocks) + "\n</script>\n"

    def _js_shared_utils(self) -> str:
        return r"""
// ── Tab / section navigation ───────────────────────────────────────────────

function showTab(btn, sectionKey, tabKey, allTabKeys) {
  allTabKeys.forEach(function(k) {
    var el = document.getElementById(sectionKey + "_" + k);
    if (el) el.style.display = "none";
  });
  var target = document.getElementById(sectionKey + "_" + tabKey);
  if (target) {
    target.style.display = "block";
    target.querySelectorAll(".plotly-graph-div").forEach(function(el) {
      if (el.id) Plotly.relayout(el.id, { autosize: true, width: null });
    });
  }
  var tabBar = document.querySelector("#" + sectionKey + " .tabs");
  if (tabBar) {
    tabBar.querySelectorAll("button").forEach(function(b) {
      b.classList.remove("active-tab");
    });
  }
  btn.classList.add("active-tab");
}

// ── Statistical utilities ─────────────────────────────────────────────────

function _lnGamma(z) {
  var c = [76.18009172947146, -86.50532032941677, 24.01409824083091,
           -1.231739572450155, 0.001208650973866179, -0.000005395239384953];
  var s = 1.000000000190015;
  for (var i = 0; i < 6; i++) s += c[i] / (z + i + 1);
  return Math.log(2.5066282746310005 * s / z) + (z + 0.5) * Math.log(z + 5.5) - (z + 5.5);
}

function _betaCF(a, b, x) {
  var m2, aa, del, qab = a + b, qap = a + 1, qam = a - 1;
  var c = 1, d = 1 - qab * x / qap;
  if (Math.abs(d) < 1e-30) d = 1e-30;
  d = 1 / d;
  var h = d;
  for (var m = 1; m <= 200; m++) {
    m2 = 2 * m;
    aa = m * (b - m) * x / ((qam + m2) * (a + m2));
    d = 1 + aa * d; if (Math.abs(d) < 1e-30) d = 1e-30; d = 1 / d;
    c = 1 + aa / c; if (Math.abs(c) < 1e-30) c = 1e-30; h *= d * c;
    aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2));
    d = 1 + aa * d; if (Math.abs(d) < 1e-30) d = 1e-30; d = 1 / d;
    c = 1 + aa / c; if (Math.abs(c) < 1e-30) c = 1e-30;
    del = d * c; h *= del;
    if (Math.abs(del - 1) < 1e-10) break;
  }
  return h;
}

function _betaInc(a, b, x) {
  if (x <= 0) return 0;
  if (x >= 1) return 1;
  var bt = Math.exp(_lnGamma(a + b) - _lnGamma(a) - _lnGamma(b)
             + a * Math.log(x) + b * Math.log(1 - x));
  if (x < (a + 1) / (a + b + 2)) return bt * _betaCF(a, b, x) / a;
  return 1 - bt * _betaCF(b, a, 1 - x) / b;
}

function _pearson(xArr, yArr, wArr) {
  var n = xArr.length;
  if (n < 3) return { r: null, p: null, n: n };

  // Fall back to uniform weights if none supplied
  var w = wArr && wArr.length === n ? wArr : null;

  var sw = 0, swx = 0, swy = 0, swx2 = 0, swy2 = 0, swxy = 0;
  for (var i = 0; i < n; i++) {
    var wi = w ? w[i] : 1;
    sw   += wi;
    swx  += wi * xArr[i];
    swy  += wi * yArr[i];
    swx2 += wi * xArr[i] * xArr[i];
    swy2 += wi * yArr[i] * yArr[i];
    swxy += wi * xArr[i] * yArr[i];
  }
  var num = sw * swxy - swx * swy;
  var den = Math.sqrt((sw * swx2 - swx * swx) * (sw * swy2 - swy * swy));
  if (den === 0) return { r: null, p: null, n: n };
  var r = num / den, df = n - 2, t2 = r * r * df / (1 - r * r);
  var p = _betaInc(df / 2, 0.5, df / (df + t2));
  return { r: r, p: p, n: n };
}

function _loess(xArr, yArr, wArr, bandwidth) {
  var n = xArr.length;
  if (n < 4) return null;
  bandwidth = bandwidth || 0.75;
  var q = Math.max(2, Math.floor(bandwidth * n));
  var hasWeights = wArr && wArr.length === n;

  var idx = xArr.map(function(_, i) { return i; })
    .sort(function(a, b) { return xArr[a] - xArr[b]; });
  var xs = idx.map(function(i) { return xArr[i]; });
  var ys = idx.map(function(i) { return yArr[i]; });
  var ws = hasWeights ? idx.map(function(i) { return wArr[i]; }) : null;

  var fitted = new Array(n);
  for (var i = 0; i < n; i++) {
    var dists = xs.map(function(x) { return Math.abs(x - xs[i]); });
    var sorted_d = dists.slice().sort(function(a, b) { return a - b; });
    var h = sorted_d[q - 1] || 1e-10;

    var sw = 0, swx = 0, swy = 0, swx2 = 0, swxy = 0;
    for (var j = 0; j < n; j++) {
      var u = dists[j] / h;
      if (u >= 1) continue;
      var tricube = Math.pow(1 - u * u * u, 3);
      // multiply tricube by observation weight if available
      var w = hasWeights ? tricube * ws[j] : tricube;
      sw   += w;  swx  += w * xs[j]; swy  += w * ys[j];
      swx2 += w * xs[j] * xs[j];     swxy += w * xs[j] * ys[j];
    }
    var denom = sw * swx2 - swx * swx;
    if (Math.abs(denom) < 1e-12) {
      fitted[i] = sw > 0 ? swy / sw : ys[i];
    } else {
      var slope_l = (sw * swxy - swx * swy) / denom;
      var int_l   = (swy - slope_l * swx) / sw;
      fitted[i]   = slope_l * xs[i] + int_l;
    }
  }
  return { x: xs, y: fitted };
}

// Populated externally if needed (e.g. via HTMLBuilder.t_crit_table).
var _T_CRIT_TABLE = {};

function _getTCrit(df) {
  df = Math.max(1, Math.round(df));
  return df >= 120 ? 1.96 : (_T_CRIT_TABLE[df] || 1.96);
}

function _welchDF(s1, n1, s2, n2) {
  var a = (s1 * s1) / n1, b = (s2 * s2) / n2;
  var den = (a * a) / (n1 - 1) + (b * b) / (n2 - 1);
  return den > 0 ? ((a + b) * (a + b)) / den : 1;
}

function _fmtNum(v)      { return (v != null && v !== undefined) ? Number(v).toFixed(2) : ""; }
function _fmtCI(r)       { return r ? (r.mean - r.ci).toFixed(2) + " &ndash; " + (r.mean + r.ci).toFixed(2) : ""; }

function _fmtDiffCI(r1, r2) {
  if (!r1 || !r2 || r1.n < 2 || r2.n < 2) return "&mdash;";
  var se = Math.sqrt((r1.std * r1.std) / r1.n + (r2.std * r2.std) / r2.n);
  var tc = _getTCrit(_welchDF(r1.std, r1.n, r2.std, r2.n));
  var d  = r1.mean - r2.mean;
  return (d - tc * se).toFixed(2) + " &ndash; " + (d + tc * se).toFixed(2);
}

// ── Graph-renderer registry ───────────────────────────────────────────────

var _GRAPH_RENDERERS = {};
function _registerRenderer(type, fn) { _GRAPH_RENDERERS[type] = fn; }

// ── View data registry ────────────────────────────────────────────────────

var _VIEW_DATA    = {};
var _VIEW_CONFIGS = {};

function _registerView(key, data, configs) {
  _VIEW_DATA[key]    = data;
  _VIEW_CONFIGS[key] = configs;
}
"""

    def _js_for_view(self, v: ViewConfig) -> str:
        all_graphs = [g for row in v.rows for g in row.graphs]  # flatten
        configs_js = json.dumps([self._graph_config_to_js_obj(g) for g in all_graphs])
        lines = [
            f"// ── View: {v.key} ────────────────────────────────────────────────",
            f"_registerView({json.dumps(v.key)}, {v.data_json}, {configs_js});",
        ]
        return "\n".join(lines)

    def _graph_config_to_js_obj(self, g: GraphConfig) -> dict[str, Any]:
        """Convert a GraphConfig to a plain dict for JSON serialisation into JS."""
        o = g.options
        base: dict[str, Any] = {"divId": g.div_id, "height": g.height}

        if isinstance(o, LineOptions):
            return {**base, "type": "line", "series": o.series,
                    "xCol": o.x_col, "xLabel": o.x_label,
                    "yLabel": o.y_label, "title": o.title,
                    "connectGaps": o.connect_gaps}

        if isinstance(o, BarOptions):
            return {**base, "type": "bar", "series": o.series,
                    "xCol": o.x_col, "xLabel": o.x_label,
                    "yLabel": o.y_label, "title": o.title,
                    "barmode": o.barmode}

        if isinstance(o, DualAxisOptions):
            return {**base, "type": "dual_axis",
                    "xCol": o.x_col, "xLabel": o.x_label,
                    "leftCol": o.left_col, "leftLabel": o.left_label,
                    "rightCol": o.right_col, "rightLabel": o.right_label,
                    "title": o.title,
                    "showOverlay": o.show_overlay_chart,
                    "overlayDivId": f"{g.div_id}-overlay"}

        if isinstance(o, ScatterOptions):
            rf_obj = None
            if o.range_filter:
                rf_obj = {
                    "weightCol": o.weight_col,
                    "loId": o.range_filter.lo_input_id,
                    "hiId": o.range_filter.hi_input_id,
                    "resultId": o.range_filter.result_div_id,
                }
            return {**base, "type": "scatter",
                    "xCol": o.x_col, "xLabel": o.x_label,
                    "yCol": o.y_col, "yLabel": o.y_label,
                    "idCol": o.id_col, "timeCol": o.time_col,
                    "title": o.title,
                    "showRegression": o.show_regression,
                    "showLoess": o.show_loess,
                    "showStatsBadge": o.show_stats_badge,
                    "rangeFilter": rf_obj}

        if isinstance(o, TableOptions):
            return {**base, "type": "table",
                    "columns": o.columns,
                    "timeCol": o.time_col, "timeLabel": o.time_label}

        if isinstance(o, ComparisonOptions):
            return {**base, "type": "comparison",
                    "groups": o.groups, "groupLabel": o.group_label,
                    "filterKeys": o.filter_keys, "filterLabel": o.filter_label,
                    "defaultFilter": o.default_filter,
                    "bucketLabel": o.bucket_label, "valueLabel": o.value_label,
                    "data": json.loads(o.data_json),
                    "tCrit": json.loads(o.t_crit_json)}

        raise TypeError(f"Unhandled GraphOptions type: {type(o)!r}")

    def _js_dispatcher(self) -> str:
        # Map each view key to its primary (first) dropdown control id, if any.
        view_primary_dropdowns: dict[str, str] = {}
        for v in self.views:
            for c in v.controls:
                if isinstance(c, DropdownControl):
                    view_primary_dropdowns[v.key] = c.control_id
                    break

        return r"""
// ── updateView — single dispatcher ────────────────────────────────────────

var _VIEW_PRIMARY_DROPDOWN = """ + json.dumps(view_primary_dropdowns) + r""";

function updateView(viewKey) {
  var data    = _VIEW_DATA[viewKey];
  var configs = _VIEW_CONFIGS[viewKey];
  if (!configs) return;

  var ddId    = _VIEW_PRIMARY_DROPDOWN[viewKey];
  var cat     = ddId ? ((document.getElementById(ddId) || {}).value || "") : "";
  var records = (data && cat) ? (data[cat] || []) : (data || []);

  configs.forEach(function(cfg) {
    var fn = _GRAPH_RENDERERS[cfg.type];
    if (fn) fn(cfg, records, cat, data);
  });
}

// ── switchView — show/hide view panels ────────────────────────────────────

function switchView(viewKey) {
  document.querySelectorAll('[id^="view-"]').forEach(function(el) {
    el.style.display = "none";
  });
  document.querySelectorAll('.view-tabs button').forEach(function(b) {
    b.classList.remove("active-tab");
  });
  var btn = document.getElementById("btn-" + viewKey);
  if (btn) btn.classList.add("active-tab");
  var panel = document.getElementById("view-" + viewKey);
  if (panel) panel.style.display = "block";
  updateView(viewKey);
}

// ── Renderer: line ─────────────────────────────────────────────────────────

_registerRenderer("line", function(cfg, records, cat) {
  var el = document.getElementById(cfg.divId);
  var xVals = records.map(function(r) { return r[cfg.xCol]; });
  var traces = cfg.series.map(function(s) {
    return { x: xVals, y: records.map(function(r) { return r[s.col]; }),
             mode: "lines+markers", name: s.label, connectgaps: cfg.connectGaps };
  });
  Plotly.newPlot(cfg.divId, traces, {
    title: cfg.title || cat,
    xaxis: { title: cfg.xLabel, tickangle: -45 },
    yaxis: { title: cfg.yLabel },
    height: cfg.height,
    legend: { x: 0.01, y: 1.15, orientation: "h" }
  });
});

// ── Renderer: bar ──────────────────────────────────────────────────────────

_registerRenderer("bar", function(cfg, records, cat) {
  var el = document.getElementById(cfg.divId);
  var xVals = records.map(function(r) { return r[cfg.xCol]; });
  var traces = cfg.series.map(function(s) {
    return { x: xVals, y: records.map(function(r) { return r[s.col]; }),
             type: "bar", name: s.label };
  });
  Plotly.newPlot(cfg.divId, traces, {
    title: cfg.title || cat,
    xaxis: { title: cfg.xLabel, tickangle: -45 },
    yaxis: { title: cfg.yLabel },
    barmode: cfg.barmode,
    height: cfg.height,
    legend: { x: 0.01, y: 1.15, orientation: "h" }
  });
});

// ── Renderer: dual_axis ────────────────────────────────────────────────────

_registerRenderer("dual_axis", function(cfg, records, cat) {
  var el = document.getElementById(cfg.divId);
  var xVals  = records.map(function(r) { return r[cfg.xCol]; });
  var yLeft  = records.map(function(r) { return r[cfg.leftCol]; });
  var yRight = records.map(function(r) { return r[cfg.rightCol]; });
  var traces = [
    { x: xVals, y: yLeft,  mode: "lines+markers", name: cfg.leftLabel,  yaxis: "y"  },
    { x: xVals, y: yRight, mode: "lines+markers", name: cfg.rightLabel, yaxis: "y2" }
  ];
  var layout = {
    title:  cfg.title || (cfg.leftLabel + " vs " + cfg.rightLabel + " \u2014 " + cat),
    xaxis:  { title: cfg.xLabel, tickangle: -45 },
    yaxis:  { title: cfg.leftLabel,  side: "left" },
    yaxis2: { title: cfg.rightLabel, side: "right", overlaying: "y" },
    height: cfg.height,
    legend: { x: 0.01, y: 1.15, orientation: "h" }
  };
  Plotly.newPlot(cfg.divId, traces, layout);

  if (cfg.showOverlay && cfg.overlayDivId) {
    Plotly.newPlot(cfg.overlayDivId, traces, Object.assign({}, layout, {
      title: cat + " \u2014 " + cfg.leftLabel + " vs " + cfg.rightLabel
    }));
  }
});

// ── Renderer: scatter ──────────────────────────────────────────────────────

_registerRenderer("scatter", function(cfg, records, cat, allData) {
  var info = (allData && allData[cat] && allData[cat][cfg.yCol])
             ? allData[cat][cfg.yCol]
             : _buildScatterInfo(records, cfg);
  _renderScatterPlot(cfg.divId, cfg, info, cat);
  if (cfg.rangeFilter && info) _initRangeFilter(cfg, info, allData, cat);
});

function _buildScatterInfo(records, cfg) {
  if (!records || !records.length) return null;
  var xArr = [], yArr = [], wArr = [], times = [], ids = [];
  var hasWeights = !!cfg.weightCol;
  records.forEach(function(r) {
    if (r[cfg.xCol] != null && r[cfg.yCol] != null) {
      xArr.push(r[cfg.xCol]);
      yArr.push(r[cfg.yCol]);
      if (hasWeights && r[cfg.weightCol] != null) wArr.push(r[cfg.weightCol]);
      if (cfg.timeCol) times.push(r[cfg.timeCol]);
      if (cfg.idCol)   ids.push(r[cfg.idCol]);
    }
  });
  var weights = (hasWeights && wArr.length === xArr.length) ? wArr : null;
  var stats = _pearson(xArr, yArr, weights);
  var slope = null, intercept = null;
  if (stats.r !== null && xArr.length >= 2) {
    // Weighted OLS
    var sw = 0, swx = 0, swy = 0, swx2 = 0, swxy = 0;
    for (var i = 0; i < xArr.length; i++) {
      var wi = weights ? weights[i] : 1;
      sw += wi; swx += wi * xArr[i]; swy += wi * yArr[i];
      swx2 += wi * xArr[i] * xArr[i]; swxy += wi * xArr[i] * yArr[i];
    }
    var denom = sw * swx2 - swx * swx;
    if (Math.abs(denom) > 1e-12) {
      slope     = (sw * swxy - swx * swy) / denom;
      intercept = (swy - slope * swx) / sw;
    }
  }
  var loessResult = _loess(xArr, yArr, weights, 0.75);
  return { x: xArr, y: yArr, timepoints: times, ids: ids,
           r: stats.r, p: stats.p, n: stats.n,
           slope: slope, intercept: intercept,
           loess_x: loessResult ? loessResult.x : null,
           loess_y: loessResult ? loessResult.y : null };
}

function _renderScatterPlot(divId, cfg, info, label) {
  var el = document.getElementById(divId);

  var hover = info.timepoints.map(function(tp, i) {
    var s = cfg.timeCol ? (cfg.timeCol + ": " + tp) : "";
    if (cfg.idCol && info.ids[i]) s += (s ? "<br>" : "") + cfg.idCol + ": " + info.ids[i];
    return s;
  });

  var traces = [{
    x: info.x, y: info.y, mode: "markers", type: "scatter", name: "Data",
    text: hover,
    hovertemplate: "%{text}<br>" + cfg.xLabel + ": %{x:.3f}<br>" + cfg.yLabel + ": %{y:.3f}<extra></extra>",
    marker: { size: 7, opacity: 0.7, color: "#4C78A8" }
  }];

  if (cfg.showRegression && info.slope !== null && info.x.length >= 2) {
    var xMin = Math.min.apply(null, info.x), xMax = Math.max.apply(null, info.x);
    var pad  = (xMax - xMin) * 0.05 || 0.1;
    traces.push({
      x: [xMin - pad, xMax + pad],
      y: [info.slope * (xMin - pad) + info.intercept, info.slope * (xMax + pad) + info.intercept],
      mode: "lines", name: "Linear",
      line: { color: "#F58518", dash: "dash", width: 2 }
    });
  }
  if (cfg.showLoess && info.loess_x && info.loess_x.length >= 2) {
    traces.push({
      x: info.loess_x, y: info.loess_y, mode: "lines", name: "LOESS",
      line: { color: "#E45756", width: 2.5, shape: "spline" }
    });
  }

  var titleText = cfg.title || (cfg.xLabel + " vs " + cfg.yLabel + " \u2014 " + label);
  if (cfg.showStatsBadge && info.r !== null) {
    var rTxt = "r = " + info.r.toFixed(4);
    var pTxt = info.p !== null
      ? "p = " + (info.p < 0.0001 ? info.p.toExponential(2) : info.p.toFixed(4))
      : "";
    titleText += "<br><span style='font-size:13px;color:#666;'>"
               + rTxt + "    " + pTxt + "    n = " + info.n + "</span>";
  }

  Plotly.newPlot(divId, traces, {
    title: { text: titleText },
    xaxis: { title: cfg.xLabel },
    yaxis: { title: cfg.yLabel },
    showlegend: true,
    legend: { orientation: "h", y: -0.2 },
    margin: { t: 80, b: 60 },
    hovermode: "closest",
    height: cfg.height
  }, { responsive: true });
}

function _initRangeFilter(cfg, info, allData, cat) {
  var rf   = cfg.rangeFilter;
  var loEl = document.getElementById(rf.loId);
  var hiEl = document.getElementById(rf.hiId);
  if (!loEl || !hiEl || !info.x.length) return;

  var xMin = Math.min.apply(null, info.x), xMax = Math.max.apply(null, info.x);
  var step = ((xMax - xMin) / 20).toFixed(4);
  loEl.value = xMin.toFixed(2); loEl.step = step;
  hiEl.value = xMax.toFixed(2); hiEl.step = step;

  // Attach listeners here instead of DOMContentLoaded — inputs are
  // guaranteed to exist at this point, and this re-runs on each view
  // switch so listeners are always fresh.
  [loEl, hiEl].forEach(function(el) {
    el.oninput = function() { _updateRangeResult(cfg, allData, cat); };
  });

  _updateRangeResult(cfg, allData, cat);
}

function _updateRangeResult(cfg, allData, cat) {
  var rf    = cfg.rangeFilter; if (!rf) return;
  var loEl  = document.getElementById(rf.loId);
  var hiEl  = document.getElementById(rf.hiId);
  var resEl = document.getElementById(rf.resultId);
  if (!loEl || !hiEl || !resEl) return;

  var lo       = parseFloat(loEl.value), hi = parseFloat(hiEl.value);
  var useRange = isFinite(lo) && isFinite(hi);
  var sd       = allData && allData[cat] ? allData[cat] : null;

  function calcFiltered(info) {
    if (!info) return { r: null, p: null, n: 0, avgX: null, avgY: null };
    var xA = info.x, yA = info.y;
    if (useRange) {
      xA = []; yA = [];
      for (var i = 0; i < info.x.length; i++) {
        if (info.x[i] >= lo && info.x[i] <= hi) { xA.push(info.x[i]); yA.push(info.y[i]); }
      }
    }
    var res = _pearson(xA, yA);
    res.avgX = xA.length ? xA.reduce(function(a, b) { return a + b; }, 0) / xA.length : null;
    res.avgY = yA.length ? yA.reduce(function(a, b) { return a + b; }, 0) / yA.length : null;
    return res;
  }

  function fmtResult(res, label) {
    var r  = res.r  !== null ? res.r.toFixed(4)  : "N/A";
    var p  = res.p  !== null ? (res.p < 0.0001 ? res.p.toExponential(2) : res.p.toFixed(4)) : "N/A";
    var ax = res.avgX !== null ? res.avgX.toFixed(2) : "N/A";
    var ay = res.avgY !== null ? res.avgY.toFixed(2) : "N/A";
    return "<strong>" + label + ":</strong>&nbsp;&nbsp;"
      + "r = " + r + "&nbsp;&nbsp;&nbsp;"
      + "p = " + p + "&nbsp;&nbsp;&nbsp;"
      + "n = " + res.n + "&nbsp;&nbsp;&nbsp;"
      + "Avg X = " + ax + "&nbsp;&nbsp;&nbsp;"
      + "Avg Y = " + ay;
  }

  var lines = [];
  if (sd && sd[cfg.yCol]) {
    lines.push(fmtResult(calcFiltered(sd[cfg.yCol]), cfg.yLabel));
    } else {
    var records = sd || [];
    var xA = [], yA = [], wA = [];
    var hasW = !!cfg.weightCol;
    records.forEach(function(r) {
      var xv = r[cfg.xCol], yv = r[cfg.yCol];
      if (xv != null && yv != null && (!useRange || (xv >= lo && xv <= hi))) {
        xA.push(xv); yA.push(yv);
        if (hasW && r[cfg.weightCol] != null) wA.push(r[cfg.weightCol]);
      }
    });
    var weights = (hasW && wA.length === xA.length) ? wA : null;
    var res = _pearson(xA, yA, weights);
    // Weighted averages for display
    if (weights) {
      var sw = 0, swx = 0, swy = 0;
      for (var i = 0; i < xA.length; i++) {
        sw += weights[i]; swx += weights[i] * xA[i]; swy += weights[i] * yA[i];
      }
      res.avgX = sw > 0 ? swx / sw : null;
      res.avgY = sw > 0 ? swy / sw : null;
    } else {
      res.avgX = xA.length ? xA.reduce(function(a, b) { return a + b; }, 0) / xA.length : null;
      res.avgY = yA.length ? yA.reduce(function(a, b) { return a + b; }, 0) / yA.length : null;
    }
    lines.push(fmtResult(res, cfg.yLabel));
  }
  resEl.innerHTML = lines.join("<br>");
}

// ── Renderer: table ────────────────────────────────────────────────────────

_registerRenderer("table", function(cfg, records) {
  var el = document.getElementById(cfg.divId);
  var hdr = "<th>" + cfg.timeLabel + "</th>";
  cfg.columns.forEach(function(c) { hdr += "<th>" + c.label + "</th>"; });
  var tbody = "";
  records.forEach(function(r) {
    var row = "<td>" + r[cfg.timeCol] + "</td>";
    cfg.columns.forEach(function(c) { row += "<td>" + _fmtNum(r[c.col]) + "</td>"; });
    tbody += "<tr>" + row + "</tr>";
  });
  el.innerHTML = "<table><thead><tr>" + hdr + "</tr></thead><tbody>" + tbody + "</tbody></table>";
});

// ── Renderer: comparison ───────────────────────────────────────────────────

_registerRenderer("comparison", function(cfg) {
  // Comparison drives itself from its own selectors; ignores view-level records.
  var u1   = document.getElementById(cfg.divId + "-unit1");
  var u2   = document.getElementById(cfg.divId + "-unit2");
  var fkEl = document.getElementById(cfg.divId + "-filter");
  if (!u1 || !u2 || !fkEl) return;

  var g1 = u1.value, g2 = u2.value, fk = fkEl.value;
  var chartEl = document.getElementById(cfg.divId + "-chart");
  var tableEl = document.getElementById(cfg.divId + "-table");

  if (!g1 || !g2 || g1 === g2) {
    chartEl.innerHTML = (g1 && g2 && g1 === g2)
      ? "<p style='color:#888;'>Please select two different " + cfg.groupLabel.toLowerCase() + "s.</p>"
      : "";
    tableEl.innerHTML = "";
    return;
  }

  var bucket = cfg.data[fk] || {};
  var d1 = bucket[g1] || [], d2 = bucket[g2] || [];

  var bkSet = {};
  d1.concat(d2).forEach(function(r) { bkSet[r.bucket] = 1; });
  var bks  = Object.keys(bkSet).sort();
  var map1 = {}, map2 = {};
  d1.forEach(function(r) { map1[r.bucket] = r; });
  d2.forEach(function(r) { map2[r.bucket] = r; });

  Plotly.newPlot(cfg.divId + "-chart", [
    { x: bks, y: bks.map(function(m) { return map1[m] ? map1[m].mean : null; }),
      mode: "lines+markers", name: g1, connectgaps: false },
    { x: bks, y: bks.map(function(m) { return map2[m] ? map2[m].mean : null; }),
      mode: "lines+markers", name: g2, connectgaps: false }
  ], {
    title:  g1 + " vs " + g2 + "  " + cfg.valueLabel + " (" + cfg.filterLabel + ": " + fk + ")",
    xaxis:  { title: cfg.bucketLabel, tickangle: -45 },
    yaxis:  { title: cfg.valueLabel },
    height: cfg.height
  });

  var hdr  = "<th>Metric</th>";
  bks.forEach(function(m) { hdr += "<th>" + m + "</th>"; });

  var rowLabels = [g1 + " Avg", g2 + " Avg", "Difference",
                   g1 + " 95% CI", g2 + " 95% CI", "Difference 95% CI"];
  var cells = rowLabels.map(function() { return ""; });
  bks.forEach(function(m) {
    var v1 = map1[m] ? map1[m].mean : null, v2 = map2[m] ? map2[m].mean : null;
    cells[0] += "<td>" + _fmtNum(v1) + "</td>";
    cells[1] += "<td>" + _fmtNum(v2) + "</td>";
    cells[2] += "<td>" + _fmtNum(v1 != null && v2 != null ? v1 - v2 : null) + "</td>";
    cells[3] += "<td>" + _fmtCI(map1[m]) + "</td>";
    cells[4] += "<td>" + _fmtCI(map2[m]) + "</td>";
    cells[5] += "<td>" + _fmtDiffCI(map1[m], map2[m]) + "</td>";
  });

  var tbody = "";
  rowLabels.forEach(function(l, i) { tbody += "<tr><td>" + l + "</td>" + cells[i] + "</tr>"; });
  tableEl.innerHTML = "<table><thead><tr>" + hdr + "</tr></thead><tbody>" + tbody + "</tbody></table>";
});
"""