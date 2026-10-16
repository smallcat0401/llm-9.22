"""Render every V3 Best-of-8 zero-pass task as a Chinese review page.

This is a review-only derivative.  It never changes the frozen tasks, model
outputs, verifier results, or search metrics.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping, Sequence


QUESTION_ZH: Mapping[str, tuple[str, str]] = {
    "v3-public-ea79960b2b5e-arithmetic": (
        "6月与7月股票回购的加权平均价格",
        "2019年6月回购801,659股，平均每股183.18美元；7月回购462,629股，平均每股194.65美元。按回购股数加权，求两个月合计的平均每股回购价格。",
    ),
    "v3-public-4b50d974aae5-arithmetic": (
        "两段年度收入增长率的算术平均",
        "分别计算2017—2018和2018—2019年总净收入的同比增长率，再求这两个增长率的算术平均值。",
    ),
    "v3-public-4b50d974aae5-cagr": (
        "2017—2019年总净收入CAGR",
        "求2017至2019年总净收入的复合年增长率（CAGR），结果按百分数保留两位小数。",
    ),
    "v3-public-564f2d6051c0-arithmetic": (
        "两段研发费用增长率的算术平均",
        "分别计算2017—2018和2018—2019年研发费用的同比增长率，再求这两个增长率的算术平均值。",
    ),
    "v3-public-564f2d6051c0-cagr": (
        "2017—2019年研发费用CAGR",
        "求2017至2019年研发费用的复合年增长率（CAGR），结果按百分数保留两位小数。",
    ),
    "v3-public-13b99cafff24-arithmetic": (
        "两段新增与调整金额变化率的算术平均",
        "分别计算2017—2018和2018—2019年 Additions and adjustments 的同比变化率，再求两个变化率的算术平均值。",
    ),
    "v3-public-13b99cafff24-cagr": (
        "2017—2019年新增与调整金额CAGR",
        "求2017至2019年 Additions and adjustments 的复合年增长率（CAGR），结果按百分数保留两位小数。",
    ),
    "v3-public-776305a10cc6-arithmetic": (
        "两段Food Care账面价值增长率的算术平均",
        "分别计算2017—2018和2018—2019年 Food Care 账面价值的同比增长率，再求两个增长率的算术平均值。",
    ),
    "v3-public-776305a10cc6-cagr": (
        "2017—2019年Food Care账面价值CAGR",
        "求2017至2019年 Food Care 账面价值的复合年增长率（CAGR），结果按百分数保留两位小数。",
    ),
    "v3-public-9a63b89ea330-arithmetic": (
        "相邻两年所得税费用均值之差",
        "先求2017—2018年所得税费用均值，再求2018—2019年均值；用后者减前者，增加记正、减少记负。",
    ),
    "v3-public-993d968c025a-arithmetic": (
        "相邻两年收入均值之差",
        "先求2017—2018年收入均值，再求2018—2019年收入均值，并计算后一个均值相对前一个均值的变化量。",
    ),
    "v3-public-f5fdb156cd45-arithmetic": (
        "相邻两年经营活动净现金流均值之差",
        "分别求2017—2018与2018—2019年经营活动净现金流均值，再计算后一个均值减前一个均值。",
    ),
    "v3-public-af1f11d98652-arithmetic": (
        "两类收入在2018—2019年的均值之差",
        "分别求2018—2019年 processing revenue 与 outsourcing & cloud revenue 的平均值，再用前者减后者。",
    ),
    "v3-public-550b417fd1d0-arithmetic": (
        "两项业务合计营业利润的变化率",
        "分别合计2018和2019财年 International 与 Foodservice 的营业利润，再求合计值从2018到2019年的百分比变化。",
    ),
    "v3-public-4a29948bb22b-arithmetic": (
        "未归属股份总价的变化率",
        "根据股份数量与单价计算2018和2019年末未归属股份总价，再求总价的百分比变化。",
    ),
    "v3-public-fee44b520741-arithmetic": (
        "2015—2019年净利润平均值",
        "求表中2015至2019年五个年度净利润的算术平均值。",
    ),
    "v3-public-9f547636b5b4-arithmetic": (
        "2015—2019年定制设施租金费用平均值",
        "把表格中的短横线视为0，求2015至2019年 build-to-suit facilities 相关租金费用的算术平均值。",
    ),
    "v3-public-aa133d54fab4-arithmetic": (
        "2019财年授予与结算RSU总价值之比",
        "用数量乘以加权平均授予日公允价值，分别得到2019财年授予和结算RSU的总价值，再求前者与后者之比。",
    ),
    "v3-public-244426e00be4-arithmetic": (
        "2018年股息支付率",
        "股息支付率定义为普通股股息总额除以可用于支付股息的净利润，求截至2018年6月年度的该比率。",
    ),
    "v3-public-c84b259d3bfe-arithmetic": (
        "所有业务营业利润合计的变化率",
        "把短横线视为0，分别合计表内全部业务在2017和2018年的营业利润，再求合计值的百分比变化。",
    ),
    "v3-public-ab005e597c33-arithmetic": (
        "未归属限制性股票奖励总价值变化率",
        "使用加权平均授予日公允价值计算2008和2009年未归属限制性股票奖励总价值，再求其百分比变化；增加记正、减少记负。",
    ),
    "v3-public-4dff5a6c3f03-arithmetic": (
        "2022票据全期利息总额",
        "2022票据每年约支付2500万美元利息，分两次等额支付；付款从2012年12月1日持续到2022年12月1日，首尾日期都计入。求总利息（百万美元）。",
    ),
    "v3-public-abe2824b6e81-arithmetic": (
        "按区间中点利率估算掉期年利息",
        "取题目所给利率区间的中点，并结合利率互换的名义本金，估算年度利息费用（百万美元）。",
    ),
    "v3-screen-curriculum-v2-tank-drain-001": (
        "水箱收水后连续排水",
        "水箱初有105升水，收到3批、每批31升；之后连续4天每天排出8升。水箱标签注明最大容量1000升。最后剩多少升？",
    ),
    "v3-gsm8k-train-1945-calculator": (
        "背包剩余容量可以买多少苹果",
        "Diego的背包最多装20磅水果。他买了1磅西瓜、1磅葡萄和1磅橙子后，还能买多少磅苹果？",
    ),
    "v3-gsm8k-train-5124-calculator": (
        "收集并施用马粪肥需要几天",
        "每匹马每天产5加仑肥料；20英亩农田每英亩需400加仑，Janet每天能施肥4英亩。若有80匹马，从开始收集到全部农田施肥完毕需要多久？",
    ),
    "v3-gsm8k-train-2706-calculator": (
        "树叶在阵风中的净前进距离",
        "每阵风先把树叶向前吹5英尺，再向后吹2英尺。经历11阵风后，树叶沿人行道净前进多少英尺？",
    ),
    "v3-gsm8k-train-1722-calculator": (
        "分段速度赛程的全程平均速度",
        "6公里赛道中，前3公里时速150公里，接下来2公里比它快50公里，最后1公里速度为前3公里速度的两倍。求全程平均速度。",
    ),
    "v3-gsm8k-train-0858-calculator": (
        "超过添加糖建议量时吃了几根糖果棒",
        "男性每日添加糖建议不超过150卡。Mark喝的饮料含2500卡，其中5%来自添加糖；每根糖果棒另含25卡添加糖。若最终添加糖摄入量比建议量高100%，他吃了几根糖果棒？",
    ),
    "v3-gsm8k-train-2623-calculator": (
        "兑换奖品还差多少张蓝票",
        "10张蓝票换1张红票，10张红票换1张黄票，10张黄票换奖品。Tom已有8张黄票、3张红票和7张蓝票，还需赚多少张蓝票才能兑换奖品？",
    ),
    "v3-gsm8k-train-7014-calculator": (
        "发放和损失气球后的余量",
        "Claire起初有50个气球，给小女孩1个时又飘走12个；随后送出9个，并从同事处拿到11个。最后有多少个气球？",
    ),
    "v3-gsm8k-train-5186-calculator": (
        "由年龄关系推算Susan五年后的年龄",
        "8年前James年龄是Janet的两倍；15年后James将满37岁；Janet满3岁时Susan出生。Susan五年后多少岁？",
    ),
    "v3-gsm8k-train-5285-calculator": (
        "由石头数推算树上鸟数",
        "院中树的数量是石头数量的三倍，树上鸟数是树与石头总数的两倍。若有40块石头，树上有多少只鸟？",
    ),
    "v3-gsm8k-train-1213-calculator": (
        "两人考试正确题数之差",
        "考试共75题。Lyssa答错20%，Precious答错12题。Lyssa比Precious多答对多少题？",
    ),
    "v3-gsm8k-train-4479-calculator": (
        "赠送玉米后还剩多少穗",
        "Bob有50蒲式耳玉米，分别送出8、3、12蒲式耳，又送出21穗；每蒲式耳14穗。还剩多少穗？",
    ),
}


GROUP_ZH = {
    "reviewed_public": "公开题审核集",
    "self_written_v2": "自建V2诊断题",
    "fresh_gsm8k_train": "新GSM8K-train题",
}


# Human review of the frozen v1 screen.  A correct formula here documents the
# intended semantics; it is not injected into the frozen model outputs.
REVIEW: Mapping[str, Mapping[str, Any]] = {
    "v3-public-13b99cafff24-arithmetic": {
        "decision": "rewrite",
        "question_ok": False,
        "gt_ok": True,
        "tool_ok": True,
        "model_weakness": False,
        "formula": "(((1074-1691)/1691)+((1691-7680)/7680))/2*100 = -57.23",
        "notes": "英文只写 average year-on-year change，没有明确是两个同比百分比的算术平均。应改写后重测，当前0/8不能完全归因于模型。",
    },
    "v3-public-244426e00be4-arithmetic": {
        "decision": "reference_sft",
        "question_ok": True,
        "gt_ok": True,
        "tool_ok": True,
        "model_weakness": True,
        "formula": "48694*0.351/51279*100 = 33.33",
        "notes": "问题定义了股息支付率，表中52周截至2018年6月的数据足够。适合作为表格取数、单位对应和比率构造的参考轨迹。",
    },
    "v3-public-4a29948bb22b-arithmetic": {
        "decision": "reference_sft",
        "question_ok": True,
        "gt_ok": True,
        "tool_ok": True,
        "model_weakness": True,
        "formula": "((0.709*275)-(0.739*225.93))/(0.739*225.93)*100 = 16.78",
        "notes": "需先由数量乘公允价值构造两年总价值，再计算变化率；题目和GT一致。",
    },
    "v3-public-4b50d974aae5-arithmetic": {
        "decision": "reference_sft",
        "question_ok": True,
        "gt_ok": True,
        "tool_ok": True,
        "model_weakness": True,
        "formula": "(((25282320-22095416)/22095416)+((22095416-19063121)/19063121))/2*100 = 15.16",
        "notes": "英文明确写了 average year-on-year percentage change，GT是两个同比增长率的算术平均，定义清楚。",
    },
    "v3-public-4dff5a6c3f03-arithmetic": {
        "decision": "reference_sft",
        "question_ok": True,
        "gt_ok": True,
        "tool_ok": True,
        "model_weakness": True,
        "formula": "(10*2+1)*(25/2) = 262.5",
        "notes": "2012-12-01至2022-12-01首尾均计入，共21次半年付款，每次12.5百万美元。表格基本是干扰信息，但题目自身完整。",
    },
    "v3-public-550b417fd1d0-arithmetic": {
        "decision": "reference_sft",
        "question_ok": True,
        "gt_ok": True,
        "tool_ok": True,
        "model_weakness": True,
        "formula": "((94.5+117.7)-(86.5+121.8))/(86.5+121.8)*100 = 1.87",
        "notes": "需要按年份先合计两个业务，再计算合计值变化率；题目和GT一致。",
    },
    "v3-public-564f2d6051c0-arithmetic": {
        "decision": "rewrite",
        "question_ok": False,
        "gt_ok": True,
        "tool_ok": True,
        "model_weakness": False,
        "formula": "(((101151-76981)/76981)+((76981-61975)/61975))/2*100 = 27.81",
        "notes": "英文写 average year-on-year increase，未明确是金额增长还是百分比增长。应补上 percentage changes 和 arithmetic mean 后重测。",
    },
    "v3-public-776305a10cc6-arithmetic": {
        "decision": "rewrite",
        "question_ok": False,
        "gt_ok": True,
        "tool_ok": True,
        "model_weakness": False,
        "formula": "(((519.7-526.9)/526.9)+((527.9-519.7)/519.7))/2*100 = 0.11",
        "notes": "average annual growth rate 常被理解为CAGR。应明确要求2017—2018和2018—2019两个同比增长率的算术平均。",
    },
    "v3-public-993d968c025a-arithmetic": {
        "decision": "rewrite",
        "question_ok": False,
        "gt_ok": True,
        "tool_ok": True,
        "model_weakness": False,
        "formula": "(1552691+1470797)/2-(1470797+1388290)/2 = 82200.5",
        "notes": "change in the average 可能被理解为差值或百分比变化，且方向不够显式。应写成2018—2019均值减2017—2018均值。",
    },
    "v3-public-9a63b89ea330-arithmetic": {
        "decision": "reference_sft",
        "question_ok": True,
        "gt_ok": True,
        "tool_ok": True,
        "model_weakness": True,
        "formula": "(1496+(-879))/2-((-879)+4764)/2 = -1634",
        "notes": "方向、正负号和两个重叠年度均值均已明确，GT正确。",
    },
    "v3-public-9f547636b5b4-arithmetic": {
        "decision": "rewrite",
        "question_ok": False,
        "gt_ok": False,
        "tool_ok": True,
        "model_weakness": False,
        "formula": "按表中带符号值：((-4482)+(-785)+0+0+0)/5 = -1053.4；按费用金额绝对值：1053.4",
        "notes": "自然语言中的 expense amount 通常理解为正金额，但GT保留了EBITDA调节表中的负号。必须明确要求带符号平均，或把GT改为正1053.4。",
    },
    "v3-public-aa133d54fab4-arithmetic": {
        "decision": "reference_sft",
        "question_ok": True,
        "gt_ok": True,
        "tool_ok": True,
        "model_weakness": True,
        "formula": "(1147976*9.67)/(881420*6.53) = 1.93",
        "notes": "ratio按无量纲倍数输出，数量取绝对值；题目、表格和GT一致。",
    },
    "v3-public-ab005e597c33-arithmetic": {
        "decision": "reference_sft",
        "question_ok": True,
        "gt_ok": True,
        "tool_ok": True,
        "model_weakness": True,
        "formula": "((1441499*44.89)-(2049255*47.72))/(2049255*47.72)*100 = -33.80",
        "notes": "明确要求总价值变化率和正负方向；GT正确。",
    },
    "v3-public-abe2824b6e81-arithmetic": {
        "decision": "rewrite",
        "question_ok": False,
        "gt_ok": False,
        "tool_ok": True,
        "model_weakness": False,
        "formula": "((5.74+7.83)/2)/100*79.9 = 5.421215，保留一位小数为5.4",
        "notes": "问题正文把利率区间漏成了空白，只能从source text补出5.74%—7.83%；同时未要求保留一位小数，而严格GT为5.4。应补全区间和舍入规则后重测。",
    },
    "v3-public-af1f11d98652-arithmetic": {
        "decision": "reference_sft",
        "question_ok": True,
        "gt_ok": True,
        "tool_ok": True,
        "model_weakness": True,
        "formula": "(594202+550058)/2-(405359+361922)/2 = 188489.5",
        "notes": "difference的顺序由processing revenue和outsourcing & cloud revenue的列举顺序确定，题目与GT一致。",
    },
    "v3-public-c84b259d3bfe-arithmetic": {
        "decision": "reference_sft",
        "question_ok": True,
        "gt_ok": True,
        "tool_ok": True,
        "model_weakness": True,
        "formula": "((724.8+479.4+86.5+121.8)-(655.4+445.8-168.9+105.1+202.6))/(655.4+445.8-168.9+105.1+202.6)*100 = 13.91",
        "notes": "题目明确短横线为0，括号为负数；需要跨行聚合后计算变化率，GT正确。",
    },
    "v3-public-ea79960b2b5e-arithmetic": {
        "decision": "rewrite",
        "question_ok": False,
        "gt_ok": True,
        "tool_ok": True,
        "model_weakness": False,
        "formula": "(801659*183.18+462629*194.65)/(801659+462629) = 187.38",
        "notes": "英文只说average share price，没有明确按回购股数加权，简单平均188.915也有表面合理性。应显式加入weighted by shares purchased后重测。",
    },
    "v3-public-f5fdb156cd45-arithmetic": {
        "decision": "rewrite",
        "question_ok": False,
        "gt_ok": True,
        "tool_ok": True,
        "model_weakness": False,
        "formula": "(12980+13600)/2-(13600+14223)/2 = -621.5",
        "notes": "change of average 没有明确是差值还是百分比、也未明确方向。建议改为：从2017—2018阶段到2018—2019阶段，经营活动净现金流的两年平均值变化了多少？增加记正，减少记负。这样只定义目标，不把解题步骤写进题面。",
    },
    "v3-public-fee44b520741-arithmetic": {
        "decision": "reference_sft",
        "question_ok": True,
        "gt_ok": True,
        "tool_ok": True,
        "model_weakness": True,
        "formula": "(-80.8-566.9-582.1-330.5+81.8)/5 = -295.7",
        "notes": "五个年度和带符号净利润行均明确，GT正确。",
    },
    "v3-public-13b99cafff24-cagr": {
        "decision": "eval_only",
        "question_ok": True,
        "gt_ok": True,
        "tool_ok": True,
        "model_weakness": True,
        "formula": "((1074/7680)^(1/2)-1)*100 = -62.60",
        "notes": "CAGR题意和GT正确，但metadata中的reference_derivation误留成算术平均公式；本题是no-tool诊断题，当前计算器不支持幂运算，不进入SFT。",
    },
    "v3-public-4b50d974aae5-cagr": {
        "decision": "eval_only",
        "question_ok": True,
        "gt_ok": True,
        "tool_ok": True,
        "model_weakness": True,
        "formula": "((25282320/19063121)^(1/2)-1)*100 = 15.16",
        "notes": "CAGR题意和GT正确，但metadata中的reference_derivation误留成算术平均公式；本题为no-tool诊断，不进入SFT。",
    },
    "v3-public-564f2d6051c0-cagr": {
        "decision": "eval_only",
        "question_ok": True,
        "gt_ok": True,
        "tool_ok": True,
        "model_weakness": True,
        "formula": "((101151/61975)^(1/2)-1)*100 = 27.75",
        "notes": "CAGR题意和GT正确，但metadata中的reference_derivation误留成算术平均公式；本题为no-tool诊断，不进入SFT。",
    },
    "v3-public-776305a10cc6-cagr": {
        "decision": "eval_only",
        "question_ok": True,
        "gt_ok": True,
        "tool_ok": True,
        "model_weakness": True,
        "formula": "((527.9/526.9)^(1/2)-1)*100 = 0.09",
        "notes": "CAGR题意和GT正确，但metadata中的reference_derivation误留成算术平均公式；本题为no-tool诊断，不进入SFT。",
    },
    "v3-screen-curriculum-v2-tank-drain-001": {
        "decision": "eval_only",
        "question_ok": True,
        "gt_ok": True,
        "tool_ok": True,
        "model_weakness": True,
        "formula": "105+3*31-8*4 = 166",
        "notes": "题目和GT正确，但它来自V2 validation，训练会造成泄漏，因此只保留为诊断/评测题。容量1000升是无害干扰信息。",
    },
    "v3-gsm8k-train-0858-calculator": {
        "decision": "reference_sft",
        "question_ok": True,
        "gt_ok": True,
        "tool_ok": True,
        "model_weakness": True,
        "formula": "(150*2-2500*0.05)/25 = 7",
        "notes": "超过建议量100%表示最终摄入为建议量的200%；题意与GT一致。",
    },
    "v3-gsm8k-train-1213-calculator": {
        "decision": "rewrite",
        "question_ok": False,
        "gt_ok": False,
        "tool_ok": True,
        "model_weakness": False,
        "formula": "Lyssa答对75*0.8=60题，Precious答对75-12=63题；Lyssa少答对63-60=3题",
        "notes": "原题问Lyssa比Precious多答对多少，但Lyssa实际少答对3题。按项目所有者决定，改为：Lyssa比Precious少答对多少题？GT保持3，随后重新测试。",
    },
    "v3-gsm8k-train-1722-calculator": {
        "decision": "reference_sft",
        "question_ok": True,
        "gt_ok": True,
        "tool_ok": True,
        "model_weakness": True,
        "formula": "6/(3/150+2/200+1/300) = 180",
        "notes": "全程平均速度必须使用总距离除以总时间，不能对分段速度做简单平均；题目和GT正确。",
    },
    "v3-gsm8k-train-1945-calculator": {
        "decision": "reference_sft",
        "question_ok": True,
        "gt_ok": True,
        "tool_ok": True,
        "model_weakness": True,
        "formula": "20-1-1-1 = 17",
        "notes": "题目很简单但8次均错，数据本身无问题。可作为低难度行为诊断或少量参考SFT，避免在训练集中重复过多。",
    },
    "v3-gsm8k-train-2623-calculator": {
        "decision": "reference_sft",
        "question_ok": True,
        "gt_ok": True,
        "tool_ok": True,
        "model_weakness": True,
        "formula": "10*10*10-(8*10*10+3*10+7) = 163",
        "notes": "需把黄票、红票统一换算成蓝票；经复算GT正确。",
    },
    "v3-gsm8k-train-2706-calculator": {
        "decision": "rewrite",
        "question_ok": False,
        "gt_ok": True,
        "tool_ok": True,
        "model_weakness": False,
        "formula": "若问净位移：(5-2)*11 = 33；若问总路程：(5+2)*11 = 77",
        "notes": "has it traveled 容易被理解为总路程，而GT按距起点的净前进距离计算。应改为how far is it from its starting point后重测。",
    },
    "v3-gsm8k-train-4479-calculator": {
        "decision": "reference_sft",
        "question_ok": True,
        "gt_ok": True,
        "tool_ok": True,
        "model_weakness": True,
        "formula": "50*14-(8+3+12)*14-21 = 357",
        "notes": "需要统一蒲式耳与穗两个单位；题目和GT正确。",
    },
    "v3-gsm8k-train-5124-calculator": {
        "decision": "reference_sft",
        "question_ok": True,
        "gt_ok": True,
        "tool_ok": True,
        "model_weakness": True,
        "formula": "(20*400)/(80*5)+20/4 = 25",
        "notes": "Once ... collected enough 明确先收集全部肥料，再开始施肥；20天收集加5天施肥，GT正确。",
    },
    "v3-gsm8k-train-5186-calculator": {
        "decision": "reference_sft",
        "question_ok": True,
        "gt_ok": True,
        "tool_ok": True,
        "model_weakness": True,
        "formula": "((37-15)-8)/2+8-3+5 = 17",
        "notes": "年龄时间点可唯一推导，题目和GT正确。",
    },
    "v3-gsm8k-train-5285-calculator": {
        "decision": "rewrite",
        "question_ok": False,
        "gt_ok": False,
        "tool_ok": True,
        "model_weakness": False,
        "formula": "GT 400要求树=4*40，再算鸟=2*(160+40)=400；若three times as many，则鸟=2*(120+40)=320",
        "notes": "three times more than 可被解释为原数加三倍（4倍），也常被理解为three times as many（3倍）。必须明确写four times as many或修改GT后重测。",
    },
    "v3-gsm8k-train-7014-calculator": {
        "decision": "reference_sft",
        "question_ok": True,
        "gt_ok": True,
        "tool_ok": True,
        "model_weakness": True,
        "formula": "50-1-12-9+11 = 39",
        "notes": "发出、飘走和补充的事件顺序清楚，GT正确。",
    },
}


DECISION_ZH = {
    "reference_sft": "人工/参考程序SFT",
    "eval_only": "仅作评测",
    "rewrite": "改写后重新进行Best-of-8",
    "delete": "删除",
}


def read_jsonl(path: Path) -> tuple[Mapping[str, Any], ...]:
    return tuple(
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


def original_question(prompt: str) -> str:
    parts = prompt.split("\n\n")
    return parts[1].strip() if len(parts) > 1 else prompt.strip()


def compact(value: Any, *, limit: int = 90) -> str:
    if value is None:
        return "—"
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    else:
        text = str(value)
    text = " ".join(text.split()).replace("|", "\\|")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def decimal_or_none(value: Any) -> Decimal | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return number if number.is_finite() else None


def tool_details(row: Mapping[str, Any]) -> tuple[str, Any, bool | None, str | None]:
    steps = row["trajectory"]["steps"]
    if not steps:
        return "—", None, None, None
    expressions: list[str] = []
    last_value: Any = None
    last_ok: bool | None = None
    last_error: str | None = None
    for step in steps:
        call = step["tool_call"]
        observation = step["observation"]
        arguments = call.get("arguments", {})
        expression = arguments.get("expression", arguments.get("query", arguments))
        expressions.append(compact(expression, limit=70))
        last_ok = bool(observation.get("ok"))
        last_error = observation.get("error_code")
        content = observation.get("content")
        if isinstance(content, Mapping) and "value" in content:
            last_value = content["value"]
        else:
            last_value = content
    return " → ".join(expressions), last_value, last_ok, last_error


def failure_label(row: Mapping[str, Any]) -> str:
    rollout = row["rollout"]
    if rollout.get("protocol_error"):
        return f"协议错误：{rollout['protocol_error']}"
    expression, tool_value, tool_ok, tool_error = tool_details(row)
    if expression == "—":
        if not row["task"].get("allowed_tools"):
            return "直接答案错误（本题无工具）"
        return "未调用工具，直接答案错误"
    if not tool_ok:
        return f"工具执行失败：{tool_error or 'unknown'}"

    target = decimal_or_none(row["task"]["ground_truth"]["value"])
    tolerance = decimal_or_none(row["task"]["ground_truth"].get("tolerance", 0))
    observed = decimal_or_none(tool_value)
    if target is not None and observed is not None and tolerance is not None:
        if abs(observed - target) > tolerance:
            return "公式/数量关系错误"
    if row["verification"].get("passed"):
        return "数值命中但严格失败（检查协议）"
    return "工具结果正确，但final错误或无效"


def render(candidates: Sequence[Mapping[str, Any]]) -> str:
    by_task: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in candidates:
        by_task[row["task"]["task_id"]].append(row)
    zero_groups = {
        task_id: sorted(rows, key=lambda row: int(row["search"]["sample_index"]))
        for task_id, rows in by_task.items()
        if not any(row["rollout"]["task_success"] for row in rows)
    }
    if len(zero_groups) != 35:
        raise ValueError(f"expected 35 zero-pass tasks, found {len(zero_groups)}")
    if set(zero_groups) != set(QUESTION_ZH):
        missing = sorted(set(zero_groups) - set(QUESTION_ZH))
        extra = sorted(set(QUESTION_ZH) - set(zero_groups))
        raise ValueError(f"translation mismatch; missing={missing}, extra={extra}")
    if set(zero_groups) != set(REVIEW):
        missing = sorted(set(zero_groups) - set(REVIEW))
        extra = sorted(set(REVIEW) - set(zero_groups))
        raise ValueError(f"review mismatch; missing={missing}, extra={extra}")
    if any(len(rows) != 8 for rows in zero_groups.values()):
        raise ValueError("every zero-pass task must contain exactly eight samples")

    first_rows = [rows[0] for rows in zero_groups.values()]
    eligible_count = sum(bool(row["task"]["metadata"]["training_eligible"]) for row in first_rows)
    diagnostic_count = len(first_rows) - eligible_count
    group_counts = Counter(row["task"]["metadata"]["seed_screen_group"] for row in first_rows)
    failure_counts = Counter(failure_label(row) for rows in zero_groups.values() for row in rows)
    decision_counts = Counter(review["decision"] for review in REVIEW.values())

    lines = [
        "# V3 Best-of-8 全失败题中文审核页",
        "",
        "> 状态：逐题初审完成，等待项目所有者复核。本页不修改冻结题目、GT、轨迹或既有指标。",
        "",
        "## 这页用来决定什么",
        "",
        "这里的“全失败”指同一道题的8次采样都没有通过**严格轨迹成功**标准。它不自动说明题目适合训练：先排除歧义、错误GT、超出工具能力等数据问题，剩下的才是可信的模型弱点。",
        "",
        "人工审核后，每题只能进入以下一种处理：",
        "",
        "- **人工/参考程序SFT**：题目和GT可信，但起始策略0/8，需人为提供正确轨迹；",
        "- **仅作评测**：题目可信，但应留作validation/test，不能拿去训练；",
        "- **改写后重测**：核心关系可用，但当前措辞或上下文有问题；",
        "- **删除**：题目、GT或来源无法可靠修复。",
        "",
        "## 总览",
        "",
        f"- 0/8题目：{len(zero_groups)}",
        f"- 训练候选：{eligible_count}",
        f"- 诊断题（不可直接训练）：{diagnostic_count}",
        f"- 公开审核题：{group_counts['reviewed_public']}",
        f"- 自建V2诊断题：{group_counts['self_written_v2']}",
        f"- 新GSM8K-train题：{group_counts['fresh_gsm8k_train']}",
        "- 共280次失败采样；下面的类别是自动初筛，不替代人工判断。",
        "",
        "### 人工审核结论",
        "",
        f"- 可编写人工/参考程序SFT轨迹：{decision_counts['reference_sft']}",
        f"- 仅作评测：{decision_counts['eval_only']}",
        f"- 必须改写后重新Best-of-8：{decision_counts['rewrite']}",
        f"- 删除：{decision_counts['delete']}",
        "",
        "> 重要：标为“改写后重测”的题，当前0/8不能作为模型能力证据，也不能直接进入SFT。",
        "",
        "### 发现的数据问题",
        "",
        "- **数量关系措辞不唯一：** 第1、7、8、9、17、18、30题；",
        "- **GT符号、方向或舍入规则与题面不一致：** 第11、14、26、34题；",
        "- **隐藏metadata参考公式错误：** 第20—23题的GT是正确CAGR，但`reference_derivation`仍误写为同比增长率算术平均；",
        "- 上述问题不会回写或覆盖冻结v1结果；修订题必须建立新版本并重新做Best-of-8。",
        "",
        "### 后续修订复测",
        "",
        "11道改写题已经作为独立v2数据重新完成Best-of-8：4道获得严格成功final，语义路径审核后保留3道Search-SFT候选；另外1道因工具结果与final符号不一致而改用参考轨迹。详见`docs/V3_REVISED_ZERO_PASS_RESULTS_ZH.md`。",
        "",
        "### 自动失败分类统计",
        "",
        "| 初筛类别 | 次数 |",
        "|---|---:|",
    ]
    for label, count in sorted(failure_counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| {label} | {count} |")

    group_order = ("reviewed_public", "self_written_v2", "fresh_gsm8k_train")
    ordered = sorted(
        zero_groups.items(),
        key=lambda item: (
            group_order.index(item[1][0]["task"]["metadata"]["seed_screen_group"]),
            not bool(item[1][0]["task"]["metadata"]["training_eligible"]),
            item[0],
        ),
    )
    lines.extend(
        [
            "",
            "### 题目导航",
            "",
            "| 编号 | 题目 | 分组 | 原用途 | 审核结论 | 8次失败概览 |",
            "|---:|---|---|---|---|---|",
        ]
    )
    for index, (task_id, rows) in enumerate(ordered, start=1):
        task = rows[0]["task"]
        metadata = task["metadata"]
        title, _ = QUESTION_ZH[task_id]
        labels = Counter(failure_label(row) for row in rows)
        label_summary = "；".join(f"{name}×{count}" for name, count in labels.items())
        review = REVIEW[task_id]
        lines.append(
            f"| {index} | [{title}](#{index}-{title.lower().replace(' ', '-')}) | "
            f"{GROUP_ZH[metadata['seed_screen_group']]} | "
            f"{'训练候选' if metadata['training_eligible'] else '仅诊断'} | "
            f"{DECISION_ZH[review['decision']]} | {label_summary} |"
        )
    lines.extend(["", "---", ""])

    for index, (task_id, rows) in enumerate(ordered, start=1):
        task = rows[0]["task"]
        metadata = task["metadata"]
        title, question_zh = QUESTION_ZH[task_id]
        eligible = bool(metadata["training_eligible"])
        labels = Counter(failure_label(row) for row in rows)
        review = REVIEW[task_id]
        label_summary = "；".join(f"{name}×{count}" for name, count in labels.items())
        lines.extend(
            [
                f"## {index}. {title}",
                "",
                f"- **用途状态：** {'训练候选审核' if eligible else '诊断题，不可直接训练'}",
                f"- **分组：** {GROUP_ZH[metadata['seed_screen_group']]}",
                f"- **Task ID：** `{task_id}`",
                f"- **Family：** `{task['family_id']}`",
                f"- **GT：** `{task['ground_truth']['value']}`（允许误差 `{task['ground_truth'].get('tolerance', 0)}`）",
                f"- **8次失败概览：** {label_summary}",
                f"- **人工审核结论：** {DECISION_ZH[review['decision']]}",
                "",
                f"**中文题意：** {question_zh}",
                "",
                f"**正确数量关系/参考公式：** `{review['formula']}`",
                "",
                f"**审核说明：** {review['notes']}",
                "",
                "| 次数 | seed | 工具公式/调用 | 工具结果 | final/解析值 | 严格失败原因 |",
                "|---:|---:|---|---:|---:|---|",
            ]
        )
        for sample_number, row in enumerate(rows, start=1):
            expression, tool_value, _, _ = tool_details(row)
            predicted = row["verification"].get("predicted_value")
            final_value = row["trajectory"].get("final_answer")
            display_final = predicted if predicted is not None else final_value
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(sample_number),
                        str(row["trajectory"]["seed"]),
                        f"`{compact(expression)}`",
                        f"`{compact(tool_value)}`",
                        f"`{compact(display_final)}`",
                        failure_label(row),
                    ]
                )
                + " |"
            )
        lines.extend(
            [
                "",
                "<details>",
                "<summary>查看原始英文题目和完整上下文</summary>",
                "",
                task["prompt"].strip(),
                "",
                "</details>",
                "",
                "<details>",
                "<summary>查看8次原始模型输出</summary>",
                "",
            ]
        )
        for sample_number, row in enumerate(rows, start=1):
            lines.extend(
                [
                    f"**第{sample_number}次：**",
                    "",
                    "```text",
                    "\n--- model turn ---\n".join(str(x) for x in row["raw_outputs"]),
                    "```",
                    "",
                ]
            )
        lines.extend(
            [
                "</details>",
                "",
                "### 人工审核",
                "",
                f"- [{'x' if review['question_ok'] else ' '}] 原始题目完整且无关键歧义",
                "- [ ] 中文题意与原题一致，没有额外泄露解法",
                f"- [{'x' if review['gt_ok'] else ' '}] GT及容差正确",
                f"- [{'x' if review['tool_ok'] else ' '}] 任务在当前指定的工具/无工具协议能力范围内",
                f"- [{'x' if review['model_weakness'] else ' '}] 0/8主要反映模型弱点，而非数据问题",
                "",
                "**最终处理（只勾一个）：**",
                "",
                f"- [{'x' if review['decision'] == 'reference_sft' else ' '}] 人工/参考程序SFT",
                f"- [{'x' if review['decision'] == 'eval_only' else ' '}] 仅作评测",
                f"- [{'x' if review['decision'] == 'rewrite' else ' '}] 改写后重新进行Best-of-8",
                f"- [{'x' if review['decision'] == 'delete' else ' '}] 删除",
                "",
                f"- **正确数量关系/参考公式：** {review['formula']}",
                f"- **审核备注：** {review['notes']}",
                "",
                "---",
                "",
            ]
        )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)

    output_text = render(read_jsonl(args.candidates))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output_text + "\n", encoding="utf-8")
    print(json.dumps({"zero_pass_tasks": 35, "output": str(args.output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
