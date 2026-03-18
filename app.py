import streamlit as st
import random
import time

# --- シミュレーション関数 ---
def simulate_accurate_damage(deck_size, cx_count, souls, trials=100000):
    total_damage = 0
    # 進捗を表示するためのプレースホルダ
    progress_bar = st.progress(0)
    
    for i in range(trials):
        # 1000回ごとに進捗バーを更新（動作を軽くするため）
        if i % 1000 == 0:
            progress_bar.progress((i + 1) / trials)
            
        deck = [1] * cx_count + [0] * (deck_size - cx_count)
        random.shuffle(deck)

        current_trial_damage = 0
        current_deck = deck[:]

        for s in souls:
            canceled = False
            for _ in range(s):
                if not current_deck:
                    break
                card = current_deck.pop()
                if card == 1:
                    canceled = True
                    break
            if not canceled:
                current_trial_damage += s
        total_damage += current_trial_damage
    
    progress_bar.empty() # 終わったらバーを消す
    return total_damage / trials

# --- UI部分 ---
st.set_page_config(page_title="WSダメージシミュレーター", layout="centered")
st.title("🎴 WS ダメージ期待値計算機")
st.caption("モンテカルロ法（10万回試行）による精密シミュレーション")

with st.sidebar:
    st.header("設定項目")
    n = st.number_input("相手の山札の残り枚数", min_value=1, max_value=50, value=20)
    k = st.number_input("相手の山札のCX枚数", min_value=0, max_value=8, value=4)
    st.divider()
    s1 = st.number_input("1人目のソウル", min_value=1, max_value=7, value=2)
    s2 = st.number_input("2人目のソウル", min_value=1, max_value=7, value=2)
    s3 = st.number_input("3人目のソウル", min_value=1, max_value=7, value=3)

# 実行ボタン
if st.button("シミュレーションを開始する", type="primary"):
    if k > n:
        st.error("エラー：CXの枚数が山札より多いです！")
    else:
        with st.spinner('計算中...'):
            start_time = time.time()
            expected_val = simulate_accurate_damage(n, k, [s1, s2, s3])
            end_time = time.time()
        
        # 結果表示
        st.balloons()
        st.success(f"### 期待値: **{expected_val:.3f}** 点")
        st.info(f"計算時間: {end_time - start_time:.2f} 秒")
