from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from StatsHelper import StatsHelper

@dataclass
class Tab:
    key: str
    label: str
    content_html: str

@dataclass
class Section:
    key: str
    label: str
    date_range: Optional[Tuple[str, str]] = None
    tabs: List[Tab] = field(default_factory=list)

    @property
    def heading(self) -> str:
        if self.date_range:
            return f"{self.label} ({self.date_range[0]} to {self.date_range[1]})"
        return self.label

    def add_tab(self, key: str, label: str, content_html: str) -> "Section":
        """Append a tab and return *self* for method chaining."""
        self.tabs.append(Tab(key, label, content_html))
        return self

@dataclass
class ComparisonConfig:
    data_json: str
    t_crit_json: str
    groups: List[str]
    filter_keys: List[Any]
    default_filter: Any
    tab_label: str
    heading: str
    filter_label: str
    value_label: str
    group_label: str
    bucket_label: str

@dataclass
class SeriesConfig:
    col: str
    label: str
    axis: str = "left"
    overlay_col: Optional[str] = None
    overlay_label: str = ""

@dataclass
class SecondaryViewConfig:
    data_json: str
    categories: List[str]
    series: List[SeriesConfig]
    tab_label: str
    heading: str
    category_label: str
    time_col: str
    time_label: str

@dataclass
class CorrelationConfig:
    scatter_json: str
    departments: List[str]
    group_names: List[str]
    hour: int
    col1_key: str
    col2_key: str
    col1_label: str
    col2_label: str
    tab_label: str
    heading: str

class HTMLBuilder:

    def __init__(
        self,
        title: str,
        main_tab_label: str,
        dropdown_label: str,
        plotly_version: str,
        template: str,
    ):
        self.title = title
        self.main_tab_label = main_tab_label
        self.dropdown_label = dropdown_label
        self.plotly_version = plotly_version
        self.template = template
        self.sections: List[Section] = []
        self.comparison: Optional[ComparisonConfig] = None
        self.secondary: Optional[SecondaryViewConfig] = None
        self.correlation: Optional[CorrelationConfig] = None

    def add_section(
        self,
        key: str,
        label: str,
        date_range: Optional[Tuple[str, str]] = None,
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
        toggle_fragment = (
            f'<div class="tab-toggle" data-label="{button_label}" '
            f'style="display:none;">{content_html}</div>'
        )
        for sec in self.sections:
            if sec.key == section_key:
                for tab in sec.tabs:
                    if tab.key == tab_key:
                        tab.content_html += toggle_fragment
                        return self
                raise KeyError(f"No tab with key '{tab_key}' in section '{section_key}'.")
        raise KeyError(f"No section with key '{section_key}' found.")

    def add_dropdown(
        self,
        section_key: str,
        tab_key: str,
        dropdown_id: str,
        label: str,
        options: List[str],
        on_change_js: str = "",
    ) -> "HTMLBuilder":
        opts_html = "\n".join(
            f'<option value="{o}">{o}</option>' for o in options
        )
        onchange_attr = f' onchange="{on_change_js}()"' if on_change_js else ""
        select_html = (
            f'<div style="margin-bottom:12px;">'
            f'<label><strong>{label}:</strong></label>'
            f'<select id="{dropdown_id}"{onchange_attr} style="padding:6px;margin-left:8px;">'
            f"{opts_html}"
            f"</select></div>"
        )
        for sec in self.sections:
            if sec.key == section_key:
                for tab in sec.tabs:
                    if tab.key == tab_key:
                        tab.content_html = select_html + tab.content_html
                        return self
                raise KeyError(f"No tab with key '{tab_key}' in section '{section_key}'.")
        raise KeyError(f"No section with key '{section_key}' found.")

    def set_comparison(
        self,
        data: dict,
        groups: List[str],
        filter_keys: List[Any],
        default_filter: Any,
        tab_label: str,
        heading: str,
        filter_label: str,
        value_label: str,
        group_label: str,
        bucket_label: str,
        t_crit: Optional[Dict[int, float]] = None,
    ) -> None:
        self.comparison = ComparisonConfig(
            data_json=json.dumps(data),
            t_crit_json=json.dumps(t_crit or StatsHelper.t_crit_table()),
            groups=groups,
            filter_keys=filter_keys,
            default_filter=default_filter,
            tab_label=tab_label,
            heading=heading,
            filter_label=filter_label,
            value_label=value_label,
            group_label=group_label,
            bucket_label=bucket_label,
        )

    def set_secondary_view(
        self,
        data: dict,
        categories: List[str],
        series: List[SeriesConfig],
        tab_label: str,
        heading: str,
        category_label: str,
        time_col: str,
        time_label: str,
    ) -> None:
        if not series:
            raise ValueError("set_secondary_view requires at least one SeriesConfig.")
        self.secondary = SecondaryViewConfig(
            data_json=json.dumps(data),
            categories=categories,
            series=series,
            tab_label=tab_label,
            heading=heading,
            category_label=category_label,
            time_col=time_col,
            time_label=time_label,
        )

    def set_correlation(
        self,
        data: dict,
        hour: int,
        col1_label: str,
        col2_label: str,
        *,
        tab_label: str = "Correlation",
        heading: str = "Correlation Analysis",
    ) -> None:
        departments = data.pop("__departments__", [])
        group_names = data.pop("__department_groups__", [])
        col1_key = data.pop("__col1__", col1_label)
        col2_key = data.pop("__col2__", col2_label)
        scatter = data.pop("__scatter__", {})
        self.correlation = CorrelationConfig(
            scatter_json=json.dumps(scatter),
            departments=departments,
            group_names=group_names,
            hour=hour,
            col1_key=col1_key,
            col2_key=col2_key,
            col1_label=col1_label,
            col2_label=col2_label,
            tab_label=tab_label,
            heading=heading,
        )

    def render(self) -> str:
        replacements = {
            "%%PLOTLY_VERSION%%": self.plotly_version,
            "%%TITLE%%": self.title,
            "%%MAIN_TAB_LABEL%%": self.main_tab_label,
            "%%DROPDOWN_LABEL%%": self.dropdown_label,
            "%%SECTION_DROPDOWN%%": self._dropdown_html(),
            "%%SECTIONS%%": self._sections_html(),
            "%%COMPARISON_BLOCK%%": self._comparison_html(),
            "%%COMPARE_TAB_BUTTON%%": self._compare_tab_button(),
            "%%SECONDARY_BLOCK%%": self._secondary_html(),
            "%%SECONDARY_TAB_BUTTON%%": self._secondary_tab_button(),
            "%%CORRELATION_BLOCK%%": self._correlation_html(),
            "%%CORRELATION_TAB_BUTTON%%": self._correlation_tab_button(),
        }
        html = self.template
        for marker, value in replacements.items():
            html = html.replace(marker, value)
        return html

    def save(self, path: str) -> None:
        from pathlib import Path
        Path(path).write_text(self.render(), encoding="utf-8")

    def _dropdown_html(self) -> str:
        return "\n".join(
            f'<option value="{s.key}">{s.label}</option>'
            for s in self.sections
        )

    def _sections_html(self) -> str:
        parts = []
        for i, sec in enumerate(self.sections):
            display = "block" if i == 0 else "none"
            tab_keys_js = json.dumps([t.key for t in sec.tabs])
            buttons = "\n".join(
                f"<button onclick=\"showTab('{sec.key}','{t.key}',"
                f"{tab_keys_js.replace(chr(34), '&quot;')})\">"
                f"{t.label}</button>"
                for t in sec.tabs
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

    def _compare_tab_button(self) -> str:
        if not self.comparison:
            return ""
        return (
            f'<button id="btn-compare" onclick="switchView(\'compare\')">'
            f"{self.comparison.tab_label}</button>"
        )

    def _secondary_tab_button(self) -> str:
        if not self.secondary:
            return ""
        return (
            f'<button id="btn-secondary" onclick="switchView(\'secondary\')">'
            f"{self.secondary.tab_label}</button>"
        )

    def _comparison_html(self) -> str:
        if not self.comparison:
            return ""
        c = self.comparison
        group_opts = "\n".join(
            f'<option value="{g}">{g}</option>' for g in c.groups
        )
        filter_opts = "\n".join(
            f'<option value="{k}"{" selected" if k == c.default_filter else ""}>'
            f"{k}</option>"
            for k in c.filter_keys
        )
        return f"""
<div id="compare-view" style="display:none;">
    <h2>{c.heading}</h2>
    <div style="margin-bottom:15px;">
        <label><strong>{c.group_label} 1:</strong></label>
        <select id="comp_unit1" onchange="updateComparison()"
                style="padding:8px;margin-right:20px;">
            <option value="">-- Select --</option>{group_opts}
        </select>
        <label><strong>{c.group_label} 2:</strong></label>
        <select id="comp_unit2" onchange="updateComparison()"
                style="padding:8px;margin-right:20px;">
            <option value="">-- Select --</option>{group_opts}
        </select>
        <label><strong>{c.filter_label}:</strong></label>
        <select id="comp_filter" onchange="updateComparison()" style="padding:8px;">
            {filter_opts}
        </select>
    </div>
    <div id="comp_chart" style="margin-top:20px;"></div>
    <div id="comp_table" style="margin-top:20px;overflow-x:auto;"></div>
</div>

<script>
var compData    = {c.data_json};
var tCritTable  = {c.t_crit_json};
var VALUE_LABEL = {json.dumps(c.value_label)};
var GROUP_LABEL = {json.dumps(c.group_label)};
var FILTER_LABEL = {json.dumps(c.filter_label)};
var BUCKET_LABEL = {json.dumps(c.bucket_label)};

function getTCrit(df) {{
    df = Math.max(1, Math.round(df));
    return df >= 120 ? 1.96 : (tCritTable[df] || 1.96);
}}
function welchDF(s1,n1,s2,n2) {{
    var a=(s1*s1)/n1, b=(s2*s2)/n2;
    var den=(a*a)/(n1-1)+(b*b)/(n2-1);
    return den>0 ? ((a+b)*(a+b))/den : 1;
}}
function fmtDiffCI(r1,r2) {{
    if(!r1||!r2||r1.n<2||r2.n<2) return "&mdash;";
    var se=Math.sqrt((r1.std*r1.std)/r1.n+(r2.std*r2.std)/r2.n);
    var tc=getTCrit(welchDF(r1.std,r1.n,r2.std,r2.n));
    var d=r1.mean-r2.mean;
    return (d-tc*se).toFixed(2)+" &ndash; "+(d+tc*se).toFixed(2);
}}

function updateComparison() {{
    var u1=document.getElementById("comp_unit1").value;
    var u2=document.getElementById("comp_unit2").value;
    var fk=document.getElementById("comp_filter").value;

    if(!u1||!u2||u1===u2) {{
        document.getElementById("comp_chart").innerHTML =
            (u1&&u2&&u1===u2)
                ? "<p style='color:#888;'>Please select two different "+GROUP_LABEL.toLowerCase()+"s.</p>"
                : "";
        document.getElementById("comp_table").innerHTML="";
        return;
    }}

    var bucket = compData[fk] || {{}};
    var d1=bucket[u1]||[], d2=bucket[u2]||[];

    var bkSet={{}};
    d1.forEach(function(r){{bkSet[r.bucket]=1;}});
    d2.forEach(function(r){{bkSet[r.bucket]=1;}});
    var bks=Object.keys(bkSet).sort();

    var map1={{}}, map2={{}};
    d1.forEach(function(r){{map1[r.bucket]=r;}});
    d2.forEach(function(r){{map2[r.bucket]=r;}});

    Plotly.newPlot("comp_chart",
        [
            {{x:bks, y:bks.map(function(m){{return map1[m]?map1[m].mean:null;}}),
              mode:"lines+markers", name:u1, connectgaps:false}},
            {{x:bks, y:bks.map(function(m){{return map2[m]?map2[m].mean:null;}}),
              mode:"lines+markers", name:u2, connectgaps:false}}
        ],
        {{title:u1+" vs "+u2+"  "+VALUE_LABEL+" ("+FILTER_LABEL+": "+fk+")",
          xaxis:{{title:BUCKET_LABEL,tickangle:-45}},
          yaxis:{{title:VALUE_LABEL}}, height:500}}
    );

    function fmt(v){{return v!=null?v.toFixed(2):"";}}
    function fmtCI(r){{return r?(r.mean-r.ci).toFixed(2)+" &ndash; "+(r.mean+r.ci).toFixed(2):"";}}

    var hdr="<th>Metric</th>";
    bks.forEach(function(m){{hdr+="<th>"+m+"</th>";}});

    var labels=[u1+" Avg",u2+" Avg","Difference",
                u1+" 95% CI",u2+" 95% CI","Difference 95% CI"];
    var cells=labels.map(function(){{return"";}});

    bks.forEach(function(m){{
        var v1=map1[m]?map1[m].mean:null, v2=map2[m]?map2[m].mean:null;
        var diff=(v1!=null&&v2!=null)?(v1-v2):null;
        cells[0]+="<td>"+fmt(v1)+"</td>";
        cells[1]+="<td>"+fmt(v2)+"</td>";
        cells[2]+="<td>"+fmt(diff)+"</td>";
        cells[3]+="<td>"+fmtCI(map1[m])+"</td>";
        cells[4]+="<td>"+fmtCI(map2[m])+"</td>";
        cells[5]+="<td>"+fmtDiffCI(map1[m],map2[m])+"</td>";
    }});

    var tbody="";
    labels.forEach(function(l,i){{tbody+="<tr><td>"+l+"</td>"+cells[i]+"</tr>";}});
    document.getElementById("comp_table").innerHTML=
        "<table><thead><tr>"+hdr+"</tr></thead><tbody>"+tbody+"</tbody></table>";
}}
</script>
"""

    def _secondary_html(self) -> str:
        if not self.secondary:
            return ""
        sv = self.secondary

        cat_opts = "\n".join(
            f'<option value="{d}"{" selected" if i == 0 else ""}>'
            f"{d}</option>"
            for i, d in enumerate(sv.categories)
        )
        overlay_divs = "\n".join(
            f'<div id="sv_overlay_{i}" style="margin-top:30px;"></div>'
            for i, s in enumerate(sv.series)
            if s.overlay_col
        )
        series_js = json.dumps([
            {
                "col": s.col,
                "label": s.label,
                "axis": s.axis,
                "overlayCol": s.overlay_col or "",
                "overlayLabel": s.overlay_label,
            }
            for s in sv.series
        ])

        return f"""
<div id="secondary-view" style="display:none;">
    <h2>{sv.heading}</h2>
    <div style="margin-bottom:15px;">
        <label><strong>{sv.category_label}:</strong></label>
        <select id="sv_cat" onchange="updateSecondary()" style="padding:8px;margin-right:20px;">
            {cat_opts}
        </select>
    </div>
    <div id="sv_chart" style="margin-top:20px;"></div>
    {overlay_divs}
    <div id="sv_table" style="margin-top:20px;overflow-x:auto;"></div>
</div>

<script>
var svData        = {sv.data_json};
var SV_SERIES     = {series_js};
var SV_TIME_COL   = {json.dumps(sv.time_col)};
var SV_TIME_LABEL = {json.dumps(sv.time_label)};
var SV_CAT_LABEL  = {json.dumps(sv.category_label)};

function updateSecondary() {{
    var cat     = document.getElementById("sv_cat").value;
    var records = svData[cat] || [];

    if (records.length === 0) {{
        document.getElementById("sv_chart").innerHTML =
            "<p style='color:#888;'>No data for this " + SV_CAT_LABEL.toLowerCase() + ".</p>";
        document.getElementById("sv_table").innerHTML = "";
        SV_SERIES.forEach(function(s, i) {{
            if (s.overlayCol) {{
                var el = document.getElementById("sv_overlay_" + i);
                if (el) el.innerHTML = "";
            }}
        }});
        return;
    }}

    var xVals = records.map(function(r) {{ return r[SV_TIME_COL]; }});

    var traces = [];
    var layout = {{
        title: cat + " \u2014 Chronological Stats",
        xaxis: {{ title: SV_TIME_LABEL, tickangle: -45 }},
        height: 520,
        legend: {{ x: 0.01, y: 1.15, orientation: "h" }}
    }};

    var leftCount = 0, rightCount = 0;
    SV_SERIES.forEach(function(s) {{
        var yVals    = records.map(function(r) {{ return r[s.col]; }});
        var isRight  = (s.axis === "right");
        var yAxisKey = isRight ? "y2" : "y";

        traces.push({{ x: xVals, y: yVals, mode: "lines+markers", name: s.label, yaxis: yAxisKey }});

        if (isRight) {{
            if (rightCount === 0) layout.yaxis2 = {{ title: s.label, side: "right", overlaying: "y" }};
            rightCount++;
        }} else {{
            if (leftCount === 0) layout.yaxis = {{ title: s.label, side: "left" }};
            leftCount++;
        }}
    }});

    Plotly.newPlot("sv_chart", traces, layout);

    SV_SERIES.forEach(function(s, i) {{
        if (!s.overlayCol) return;
        var divId = "sv_overlay_" + i;
        var el    = document.getElementById(divId);
        if (!el) return;

        var yVals = records.map(function(r) {{ return r[s.col]; }});
        var oVals = records.map(function(r) {{ return r[s.overlayCol]; }});

        Plotly.newPlot(divId, [
            {{ x: xVals, y: yVals, mode: "lines+markers", name: s.label,        yaxis: "y"  }},
            {{ x: xVals, y: oVals, mode: "lines+markers", name: s.overlayLabel, yaxis: "y2" }}
        ], {{
            title:  cat + " \u2014 " + s.label + " vs " + s.overlayLabel,
            xaxis:  {{ title: SV_TIME_LABEL, tickangle: -45 }},
            yaxis:  {{ title: s.label,        side: "left"  }},
            yaxis2: {{ title: s.overlayLabel, side: "right", overlaying: "y" }},
            height: 520,
            legend: {{ x: 0.01, y: 1.15, orientation: "h" }}
        }});
    }});

    var hdr = "<th>" + SV_TIME_LABEL + "</th>";
    SV_SERIES.forEach(function(s) {{ hdr += "<th>" + s.label + "</th>"; }});
    var shownOverlays = {{}};
    SV_SERIES.forEach(function(s) {{
        if (s.overlayCol && !shownOverlays[s.overlayCol]) {{
            hdr += "<th>" + s.overlayLabel + "</th>";
            shownOverlays[s.overlayCol] = true;
        }}
    }});

    function fmt(v) {{ return (v != null && v !== undefined) ? Number(v).toFixed(2) : ""; }}
    var tbody = "";
    records.forEach(function(r) {{
        var row = "<td>" + r[SV_TIME_COL] + "</td>";
        SV_SERIES.forEach(function(s) {{ row += "<td>" + fmt(r[s.col]) + "</td>"; }});
        var seenOverlay = {{}};
        SV_SERIES.forEach(function(s) {{
            if (s.overlayCol && !seenOverlay[s.overlayCol]) {{
                row += "<td>" + fmt(r[s.overlayCol]) + "</td>";
                seenOverlay[s.overlayCol] = true;
            }}
        }});
        tbody += "<tr>" + row + "</tr>";
    }});
    document.getElementById("sv_table").innerHTML =
        "<table><thead><tr>" + hdr + "</tr></thead><tbody>" + tbody + "</tbody></table>";
}}

document.addEventListener("DOMContentLoaded", function() {{
    var origSwitch = window.switchView;
    window.switchView = function(view) {{
        if (origSwitch) origSwitch(view);
        if (view === "secondary") updateSecondary();
    }};
}});
</script>
"""
    def _correlation_tab_button(self) -> str:
        if not self.correlation:
            return ""
        return (
            f'<button id="btn-correlation" '
            f"onclick=\"switchView('correlation'); setTimeout(window._corrRender, 100);\">"
            f"{self.correlation.tab_label}</button>"
        )

    def _correlation_html(self) -> str:
        if not self.correlation:
            return ""
        c = self.correlation

        dept_options = (
            '<option value="Overall">Overall (all departments)</option>'
            + "".join(f'<option value="{g}">{g}</option>' for g in c.group_names)
            + "".join(f'<option value="{d}">{d}</option>' for d in c.departments)
        )

        js = (
            "<script>\n"
            "var _CORR_SCATTER  = " + c.scatter_json + ";\n"
            "var _CORR_HOUR     = " + str(c.hour) + ";\n"
            "var _CORR_COL1_KEY = " + json.dumps(c.col1_key) + ";\n"
            "var _CORR_COL2_KEY = " + json.dumps(c.col2_key) + ";\n"
            "var _CORR_COL1_LBL = " + json.dumps(c.col1_label) + ";\n"
            "var _CORR_COL2_LBL = " + json.dumps(c.col2_label) + ";\n"
            "\n"
            "function _lnGamma(z) {\n"
            "  var c = [76.18009172947146,-86.50532032941677,24.01409824083091,\n"
            "           -1.231739572450155,0.001208650973866179,-0.000005395239384953];\n"
            "  var s = 1.000000000190015;\n"
            "  for (var i=0;i<6;i++) s+=c[i]/(z+i+1);\n"
            "  return Math.log(2.5066282746310005*s/z)+(z+0.5)*Math.log(z+5.5)-(z+5.5);\n"
            "}\n"
            "function _betaCF(a,b,x) {\n"
            "  var m2,aa,del,qab=a+b,qap=a+1,qam=a-1;\n"
            "  var c=1,d=1-qab*x/qap; if(Math.abs(d)<1e-30)d=1e-30;\n"
            "  d=1/d; var h=d;\n"
            "  for(var m=1;m<=200;m++) {\n"
            "    m2=2*m;\n"
            "    aa=m*(b-m)*x/((qam+m2)*(a+m2));\n"
            "    d=1+aa*d; if(Math.abs(d)<1e-30)d=1e-30; d=1/d;\n"
            "    c=1+aa/c; if(Math.abs(c)<1e-30)c=1e-30;\n"
            "    h*=d*c;\n"
            "    aa=-(a+m)*(qab+m)*x/((a+m2)*(qap+m2));\n"
            "    d=1+aa*d; if(Math.abs(d)<1e-30)d=1e-30; d=1/d;\n"
            "    c=1+aa/c; if(Math.abs(c)<1e-30)c=1e-30;\n"
            "    del=d*c; h*=del;\n"
            "    if(Math.abs(del-1)<1e-10)break;\n"
            "  }\n"
            "  return h;\n"
            "}\n"
            "function _betaInc(a,b,x) {\n"
            "  if(x<=0)return 0; if(x>=1)return 1;\n"
            "  var bt=Math.exp(_lnGamma(a+b)-_lnGamma(a)-_lnGamma(b)\n"
            "         +a*Math.log(x)+b*Math.log(1-x));\n"
            "  if(x<(a+1)/(a+b+2)) return bt*_betaCF(a,b,x)/a;\n"
            "  return 1-bt*_betaCF(b,a,1-x)/b;\n"
            "}\n"
            "function _pearson(xArr,yArr) {\n"
            "  var n=xArr.length;\n"
            "  if(n<3) return {r:null,p:null,n:n};\n"
            "  var sx=0,sy=0,sxy=0,sx2=0,sy2=0;\n"
            "  for(var i=0;i<n;i++) {\n"
            "    sx+=xArr[i]; sy+=yArr[i];\n"
            "    sxy+=xArr[i]*yArr[i]; sx2+=xArr[i]*xArr[i]; sy2+=yArr[i]*yArr[i];\n"
            "  }\n"
            "  var num=n*sxy-sx*sy;\n"
            "  var den=Math.sqrt((n*sx2-sx*sx)*(n*sy2-sy*sy));\n"
            "  if(den===0) return {r:null,p:null,n:n};\n"
            "  var r=num/den, df=n-2, t2=r*r*df/(1-r*r);\n"
            "  var p=_betaInc(df/2,0.5,df/(df+t2));\n"
            "  return {r:r,p:p,n:n};\n"
            "}\n"
            "function _corrScatter(divId,info,metricLabel,deptLabel) {\n"
            "  if(!info) return;\n"
            "  var hover=info.timepoints.map(function(ym,i) {\n"
            "    var s='YearMonth: '+ym;\n"
            "    if(info.ids&&info.ids[i]) s+='<br>Dept: '+info.ids[i];\n"
            "    return s;\n"
            "  });\n"
            "  var traces=[{x:info.x,y:info.y,mode:'markers',type:'scatter',name:'Data',\n"
            "    text:hover,\n"
            "    hovertemplate:'%{text}<br>Workload: %{x:.3f}<br>'+metricLabel+': %{y:.3f}<extra></extra>',\n"
            "    marker:{size:7,opacity:0.7,color:'#4C78A8'}}];\n"
            "  if(info.slope!==null&&info.x.length>=2) {\n"
            "    var xMin=Math.min.apply(null,info.x), xMax=Math.max.apply(null,info.x);\n"
            "    var pad=(xMax-xMin)*0.05||0.1;\n"
            "    traces.push({x:[xMin-pad,xMax+pad],\n"
            "      y:[info.slope*(xMin-pad)+info.intercept,info.slope*(xMax+pad)+info.intercept],\n"
            "      mode:'lines',name:'Linear',line:{color:'#F58518',dash:'dash',width:2}});\n"
            "  }\n"
            "  if(info.loess_x&&info.loess_x.length>=2) {\n"
            "    traces.push({x:info.loess_x,y:info.loess_y,mode:'lines',name:'LOESS',\n"
            "      line:{color:'#E45756',width:2.5,shape:'spline'}});\n"
            "  }\n"
            "  var rTxt=info.r!==null?'r = '+info.r.toFixed(4):'r = N/A';\n"
            "  var pTxt=info.p!==null\n"
            "    ?'p = '+(info.p<0.0001?info.p.toExponential(2):info.p.toFixed(4)):'';\n"
            "  var sub=rTxt+'    '+pTxt+'    n = '+info.n;\n"
            "  Plotly.newPlot(divId,traces,{\n"
            "    title:{text:'Workload @'+_CORR_HOUR+':00  vs  '+metricLabel\n"
            "           +' ('+deptLabel+')<br>'\n"
            "           +'<span style=\"font-size:13px;color:#666;\">'+sub+'</span>'},\n"
            "    xaxis:{title:'Avg Workload per Employee (@'+_CORR_HOUR+':00)'},\n"
            "    yaxis:{title:metricLabel},\n"
            "    showlegend:true,legend:{orientation:'h',y:-0.2},\n"
            "    margin:{t:80,b:60},hovermode:'closest'\n"
            "  },{responsive:true});\n"
            "}\n"
            "function _corrUpdateRange() {\n"
            "  var deptKey=document.getElementById('corr-dept-select').value;\n"
            "  var lo=parseFloat(document.getElementById('corr-range-lo').value);\n"
            "  var hi=parseFloat(document.getElementById('corr-range-hi').value);\n"
            "  var sd=_CORR_SCATTER[deptKey];\n"
            "  if(!sd) return;\n"
            "  var useRange=isFinite(lo)&&isFinite(hi);\n"
            "  function avg(arr){if(!arr.length)return null;var s=0;for(var i=0;i<arr.length;i++)s+=arr[i];return s/arr.length;}\n"
            "  function calc(info) {\n"
            "    if(!info) return {r:null,p:null,n:0,avgX:null,avgY:null};\n"
            "    var xArr=info.x,yArr=info.y;\n"
            "    if(useRange){xArr=[];yArr=[];for(var i=0;i<info.x.length;i++){if(info.x[i]>=lo&&info.x[i]<=hi){xArr.push(info.x[i]);yArr.push(info.y[i]);}}}\n"
            "    var res=_pearson(xArr,yArr); res.avgX=avg(xArr); res.avgY=avg(yArr); return res;\n"
            "  }\n"
            "  function fmt(res,label) {\n"
            "    var r=res.r!==null?res.r.toFixed(4):'N/A';\n"
            "    var p=res.p!==null?(res.p<0.0001?res.p.toExponential(2):res.p.toFixed(4)):'N/A';\n"
            "    var ax=res.avgX!==null?res.avgX.toFixed(2):'N/A';\n"
            "    var ay=res.avgY!==null?res.avgY.toFixed(2):'N/A';\n"
            "    return '<strong>'+label+':</strong>&nbsp;&nbsp;'\n"
            "           +'r = '+r+'&nbsp;&nbsp;&nbsp;'\n"
            "           +'p = '+p+'&nbsp;&nbsp;&nbsp;'\n"
            "           +'n = '+res.n+'&nbsp;&nbsp;&nbsp;'\n"
            "           +'Avg Workload = '+ax+'&nbsp;&nbsp;&nbsp;'\n"
            "           +'Avg Falls/Pressure = '+ay;\n"
            "  }\n"
            "  var r1=calc(sd[_CORR_COL1_KEY]), r2=calc(sd[_CORR_COL2_KEY]);\n"
            "  document.getElementById('corr-range-result').innerHTML=fmt(r1,_CORR_COL1_LBL)+'<br>'+fmt(r2,_CORR_COL2_LBL);\n"
            "}\n"
            "function _corrSetDefaults() {\n"
            "  var deptKey=document.getElementById('corr-dept-select').value;\n"
            "  var sd=_CORR_SCATTER[deptKey];\n"
            "  if(!sd) return;\n"
            "  var info=sd[_CORR_COL1_KEY]||sd[_CORR_COL2_KEY];\n"
            "  if(!info||!info.x.length) return;\n"
            "  var xMin=Math.min.apply(null,info.x), xMax=Math.max.apply(null,info.x);\n"
            "  var loEl=document.getElementById('corr-range-lo'), hiEl=document.getElementById('corr-range-hi');\n"
            "  loEl.value=xMin.toFixed(2); hiEl.value=xMax.toFixed(2);\n"
            "  loEl.step=((xMax-xMin)/20).toFixed(4); hiEl.step=loEl.step;\n"
            "}\n"
            "window._corrRender=function() {\n"
            "  var deptKey=document.getElementById('corr-dept-select').value;\n"
            "  var sd=_CORR_SCATTER[deptKey];\n"
            "  if(sd){_corrScatter('corr-chart-1',sd[_CORR_COL1_KEY],_CORR_COL1_LBL,sd.label);\n"
            "          _corrScatter('corr-chart-2',sd[_CORR_COL2_KEY],_CORR_COL2_LBL,sd.label);}\n"
            "  _corrSetDefaults(); _corrUpdateRange();\n"
            "};\n"
            "document.getElementById('corr-dept-select').addEventListener('change',window._corrRender);\n"
            "document.getElementById('corr-range-lo').addEventListener('input',_corrUpdateRange);\n"
            "document.getElementById('corr-range-hi').addEventListener('input',_corrUpdateRange);\n"
            "</script>\n"
        )

        return (
            '<div id="correlation-view" style="display:none;">\n'
            f'  <h2 style="margin:18px 0 8px;">{c.heading}</h2>\n'
            f'  <p style="margin:0 0 12px;color:#555;">\n'
            f'    Avg workload per employee at {c.hour}:00 vs monthly {c.col1_label} and {c.col2_label} averages.\n'
            f'  </p>\n'
            f'  <div style="margin-bottom:16px;">\n'
            f'    <label for="corr-dept-select" style="font-weight:600;">Department:&nbsp;</label>\n'
            f'    <select id="corr-dept-select" style="padding:4px 8px;font-size:14px;">\n'
            f'      {dept_options}\n'
            f'    </select>\n'
            f'  </div>\n'
            f'  <div style="display:flex;flex-wrap:wrap;gap:24px;">\n'
            f'    <div id="corr-chart-1" style="flex:1 1 480px;min-width:360px;height:480px;"></div>\n'
            f'    <div id="corr-chart-2" style="flex:1 1 480px;min-width:360px;height:480px;"></div>\n'
            f'  </div>\n'
            f'  <div style="margin-top:24px;padding:16px 20px;background:#f8f9fa;border:1px solid #dee2e6;border-radius:8px;">\n'
            f'    <div style="display:flex;flex-wrap:wrap;gap:16px;align-items:center;margin-bottom:12px;">\n'
            f'      <span style="font-weight:600;">Workload range:</span>\n'
            f'      <label>From&nbsp;<input id="corr-range-lo" type="number" step="0.01" style="width:90px;padding:4px 6px;font-size:14px;"></label>\n'
            f'      <label>To&nbsp;<input id="corr-range-hi" type="number" step="0.01" style="width:90px;padding:4px 6px;font-size:14px;"></label>\n'
            f'    </div>\n'
            f'    <div id="corr-range-result" style="font-size:15px;line-height:1.8;font-family:monospace;"></div>\n'
            f'  </div>\n'
            f'</div>\n'
            + js
        )
