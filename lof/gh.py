import datetime as dt
import xalpha as xa
import re

from .predict import get_qdii_tt, get_qdii_t
from .holdings import holdings
from .exceptions import NonAccurate


def render(text, code=None):
    r = ""
    s = 0
    ls = [
        (m.start(0), m.end(0), text[m.start(0) : m.end(0)])
        for m in re.finditer(r"<!--update[^>]*>[^<]*<!--end-->", text)
    ]
    for l in ls:
        r += text[s : l[0]]
        r += replace_text(l[2], code)
        s = l[1]
    r += text[s:]
    return r


def next_onday(dtobj):
    dtobj += dt.timedelta(1)
    while dtobj.strftime("%Y-%m-%d") not in xa.cons.opendate:
        dtobj += dt.timedelta(1)
    return dtobj


def replace_text(otext, code=None, est_holdings=None, rt_holdings=None):
    print(otext)
    tzbj = dt.timezone(dt.timedelta(hours=8))
    dtstr = otext.split(":")[1].split(";")[0]
    dtobj = dt.datetime.strptime(dtstr, "%Y-%m-%d-%H-%M")
    now = dt.datetime.now(tz=tzbj)
    now = now.replace(tzinfo=None)
    if now >= dtobj:
        v = otext.split(">")[0].split(";")[1].split("-")[-3]
        vdtstr = otext.split(";")[1][:10]  # -
        if not est_holdings:
            est_holdings = holdings[code[2:]]
        if v == "value1":
            if not rt_holdings:
                rt_holdings = holdings["oil_rt"]
            # 实时净值
            if now.hour > 8:
                try:
                    _, ntext = get_qdii_t(
                        code, est_holdings, rt_holdings
                    )
                    ntext = str(round(ntext, 3))
                    ntext += f" ({now.strftime('%H:%M')})"
                    ntext = (
                        otext.split(">")[0]
                        + ">"
                        + ntext
                        + "<"
                        + otext.split("<")[-1]
                    )
                except NonAccurate:
                    ntext = otext
            else:
                # 新的一天
                ntext = otext.split(">")[1].split("<")[0]
        elif v == "value2":
            try:
                ntext = str(round(get_qdii_tt(code, est_holdings), 3))
            except NonAccurate:
                ntext = otext
        elif v == "value3":
            # 真实净值
            line = xa.get_daily(code="F" + code[2:], end=vdtstr).iloc[-1]
            if line["date"].strftime("%Y-%m-%d") != vdtstr:
                ntext = otext
            else:
                ntext = str(line["close"])
        elif v == "new":
            ntext = f"""
<tr>
<td style='text-align:center;' >{dtobj.strftime("%Y-%m-%d")}</td>
<td style='text-align:center;' ><!--update:{(dtobj + dt.timedelta(hours=1)).strftime("%Y-%m-%d-%H-%M")};{dtobj.strftime("%Y-%m-%d")}-value1-->&nbsp;<!--end--></td>
<td style='text-align:center;' ><!--update:{(dtobj + dt.timedelta(days=1, hours=1)).strftime(
        "%Y-%m-%d-%H-%M"
    )};{dtobj.strftime("%Y-%m-%d")}-value2-->&nbsp;<!--end--></td>
<td style='text-align:center;' ><!--update:{next_onday(next_onday(dtobj)).strftime("%Y-%m-%d-%H-%M")};{dtobj.strftime("%Y-%m-%d")}-value3-->&nbsp;<!--end--></td>
</tr>
<!--update:{next_onday(dtobj).strftime("%Y-%m-%d-%H-%M")};{next_onday(dtobj).strftime("%Y-%m-%d")}-new--><!--end-->
            """

    else:
        ntext = otext
    print("replaced as %s" % ntext)
    return ntext