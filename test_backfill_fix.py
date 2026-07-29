# -*- coding: utf-8 -*-
"""验证公众号文章抓取的分页/停止逻辑修复（不触网、不写库）"""
import sys, json
from datetime import date

sys.path.insert(0, '.')

import core.wx.base as basemod
import core.wx.model.app as appmod
from core.wx.base import WxGather

# ---- 屏蔽副作用：不写 Feed、不清 RSS 缓存、不改登录状态、不 sleep ----
WxGather.Start = lambda self, mp_id=None: None
WxGather.Over = lambda self, CallBack=None: None
WxGather.Item_Over = lambda self, item=None, CallBack=None: None
basemod.setStatus = lambda *a, **k: None
appmod.time.sleep = lambda *a, **k: None
appmod.random.randint = lambda a, b: 0

from core.wx.model.app import MpsAppMsg

NOW = 1785000000   # 2026-07 附近，在采集起始日期之后
OLD = 1733000000   # 2024-12，在采集起始日期之前


def make_page(n, start_aid, ts):
    lst = []
    for k in range(n):
        aid = f"testaid{start_aid + k}"
        lst.append({"publish_info": json.dumps({"appmsgex": [{
            "aid": aid, "title": f"t{aid}",
            "link": f"https://mp.weixin.qq.com/s/{aid}",
            "update_time": ts, "create_time": ts, "cover": "", "digest": ""
        }]})})
    return {"base_resp": {"ret": 0}, "publish_page": json.dumps({"publish_list": lst})}


EMPTY = {"base_resp": {"ret": 0}, "publish_page": json.dumps({"publish_list": []})}


class FakeResp:
    def __init__(self, payload):
        self._p = payload
        self.cookies = []

    def json(self):
        return self._p


class FakeSession:
    """按 begin 参数返回对应页，超出后返回空列表"""

    def __init__(self, pages):
        self.pages = pages
        self.calls = []

    def get(self, url, headers=None, params=None, verify=None):
        begin = int(params.get("begin", 0))
        page = begin // 5
        self.calls.append(page)
        payload = self.pages[page] if page < len(self.pages) else EMPTY
        return FakeResp(payload)


def make_wx(pages):
    wx = MpsAppMsg.__new__(MpsAppMsg)
    wx.session = FakeSession(pages)
    wx.token = "fake"
    wx.headers = {}
    wx.Gather_Content = False
    wx.articles = []
    wx.aids = []
    wx._cookies = []
    wx.get_collect_start_date = lambda: date(2025, 12, 1)
    return wx


collect = lambda art: True  # noqa: E731

# ---- 用例1：首次同步（库里无文章），3页数据后为空 → 应抓满3页共15篇，并因空列表终止 ----
wx = make_wx([make_page(5, 0, NOW), make_page(5, 5, NOW), make_page(5, 10, NOW)])
wx.get_Articles("fake_faker_id", Mps_id="MP_WXS_FAKE_TEST_INIT", Mps_title="测试号",
                CallBack=collect, MaxPage=1, interval=0)
assert len(wx.articles) == 15, f"用例1失败: 期望15篇, 实际{len(wx.articles)}篇"
assert wx.session.calls == [0, 1, 2, 3], f"用例1失败: 翻页序列 {wx.session.calls}"
print(f"用例1 通过: 首次同步不受 MaxPage=1 限制, 抓满3页共{len(wx.articles)}篇, 空列表正确终止")

# ---- 用例2：首次同步，第2页出现起始日期之前的文章 → 处理完该页后停止 ----
wx = make_wx([make_page(5, 0, NOW), make_page(5, 5, OLD), make_page(5, 10, NOW)])
wx.get_Articles("fake_faker_id", Mps_id="MP_WXS_FAKE_TEST_INIT", Mps_title="测试号",
                CallBack=collect, MaxPage=1, interval=0)
assert len(wx.articles) == 10, f"用例2失败: 期望10篇, 实际{len(wx.articles)}篇"
assert wx.session.calls == [0, 1], f"用例2失败: 翻页序列 {wx.session.calls}"
print(f"用例2 通过: 遇到起始日期{date(2025,12,1)}之前的文章后停止, 共{len(wx.articles)}篇")

# ---- 用例3：增量同步（库里已有文章的公众号），MaxPage=1 → 只抓1页 ----
# 诺万资产 MP_WXS_3004728055 库中已有文章（只读 count 查询）
wx = make_wx([make_page(5, 0, NOW), make_page(5, 5, NOW), make_page(5, 10, NOW)])
wx.get_Articles("fake_faker_id", Mps_id="MP_WXS_3004728055", Mps_title="诺万资产",
                CallBack=collect, MaxPage=1, interval=0)
assert len(wx.articles) == 5, f"用例3失败: 期望5篇, 实际{len(wx.articles)}篇"
assert wx.session.calls == [0], f"用例3失败: 翻页序列 {wx.session.calls}"
print(f"用例3 通过: 增量同步遵守 MaxPage=1, 只抓最新1页共{len(wx.articles)}篇")

print("\n全部用例通过 ✔")
