# -*- coding: utf-8 -*-
"""修掉 fmtTime 重名：把时间格式化助手改成 fmtClock，避免覆盖原有的 fmtTime(iso)。"""
from pathlib import Path

p = Path(r"D:\大肥鱼\jingsai\assets\app.js")
t = p.read_text(encoding="utf-8")

old_block = """  function fmtTime(t) {
    return t.getFullYear() + "-" + pad2(t.getMonth() + 1) + "-" + pad2(t.getDate()) + " " +
      pad2(t.getHours()) + ":" + pad2(t.getMinutes()) + ":" + pad2(t.getSeconds());
  }
"""
new_block = """  function fmtClock(t) {
    return t.getFullYear() + "-" + pad2(t.getMonth() + 1) + "-" + pad2(t.getDate()) + " " +
      pad2(t.getHours()) + ":" + pad2(t.getMinutes()) + ":" + pad2(t.getSeconds());
  }
"""
assert old_block in t, "未找到重复定义块"
t = t.replace(old_block, new_block, 1)
t = t.replace("if (t.getTime() > d.getTime()) return fmtTime(t);",
              "if (t.getTime() > d.getTime()) return fmtClock(t);")
t = t.replace("return fmtTime(new Date(d.getFullYear(), d.getMonth(), d.getDate() + 1, 8, 0, 0, 0));",
              "return fmtClock(new Date(d.getFullYear(), d.getMonth(), d.getDate() + 1, 8, 0, 0, 0));")
p.write_text(t, encoding="utf-8")
print("fmtTime 定义数:", t.count("function fmtTime("), "| fmtClock 定义数:", t.count("function fmtClock("))
