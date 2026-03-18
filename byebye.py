import streamlit as st
import random

# --- 計算用関数 ---
def simulate_win_rate_perfect(n_deck, k_cx, d_total, d_cx, s_list, mem_count, current_lvl, current_clock, trials=20000):
    wins = 0
    x_count = max(0, mem_count - 1)
    
    for _ in range(trials):
        # 山札の構築 (1: CX, 0: 通常)
        deck = [1] * k_cx + [0] * (n_deck - k_cx)
        random.shuffle(deck)
        
        # 控え室の構築
        discard_pile = [1] * d_cx + [0] * (d_total - d_cx)
        
        temp_lvl = current_lvl
        temp_clock = current_clock
        
        def process_damage(dmg_val, d_pile, lvl, clock):
            """ダメージ処理とレベルアップ判定"""
            for _ in range(dmg_val):
                clock += 1
                if clock >= 7:
                    lvl += 1
                    clock = 0
                    d_pile.extend([0] * 6) # レベルアップ時に6枚を控え室へ
                if lvl >= 4:
                    return lvl, clock, True
            return lvl, clock, False

        def refresh_check(d, discard, lvl, clock):
            """山札切れ判定とリフレッシュ処理"""
            if not d:
                # リフレッシュダメージ(1点)
                lvl, clock, is_dead = process_damage(1, discard, lvl, clock)
                # 控え室を混ぜて新しい山札へ
                new_deck = discard[:]
                random.shuffle(new_deck)
                return new_deck, [], lvl, clock, is_dead
            return d, discard, lvl, clock, False

        is_finished = False
        for s in s_list:
            if is_finished: break
            
            # ① 1点バーン
            deck, discard_pile, temp_lvl, temp_clock, is_finished = refresh_check(deck, discard_pile, temp_lvl, temp_clock)
            if is_finished: break
            card = deck.pop()
            if card == 1: discard_pile.append(1) # キャンセル
            else: temp_lvl, temp_clock, is_finished = process_damage(1, discard_pile, temp_lvl, temp_clock)
            
            if is_finished: break

            # ② 山札削り (思い出-1枚)
            found_cx = False
            for _ in range(x_count):
                deck, discard_pile, temp_lvl, temp_clock, is_finished = refresh_check(deck, discard_pile, temp_lvl, temp_clock)
                if is_finished: break
                removed = deck.pop()
                if removed == 1: found_cx = True
                discard_pile.append(removed)
            
            if is_finished: break

            # ③ 条件付き1点バーン
            if found_cx:
                deck, discard_pile, temp_lvl, temp_clock, is_finished = refresh_check(deck, discard_pile, temp_lvl, temp_clock)
                if is_finished: break
                card = deck.pop()
                if card == 1: discard_pile.append(1)
                else: temp_lvl, temp_clock, is_finished = process_damage(1, discard_pile, temp_lvl, temp_clock)
            
            if is_finished: break

            # ④ 本体アタック
            damage_check = []
            for _ in range(s):
                deck, discard_pile, temp_lvl, temp_clock, is_finished = refresh_check(deck, discard_pile, temp_lvl, temp_clock)
                if is_finished: break
                damage_check.append(deck.pop())
            
            if is_finished: break
            if 1 in damage_check:
                discard_pile.extend(damage_check) # キャンセル
            else:
                temp_lvl, temp_clock, is_finished = process_damage(s, discard_pile, temp_lvl, temp_clock)

        if is_finished:
            wins += 1
            
    return (wins / trials) * 100

# --- UI ---
st.set_page_config(page_title="バイビー勝利確率計算機", layout="centered")
st.title("🎴 バイビー 勝利確率計算機")

with st.sidebar:
    st.header("1. 相手の状態")
    current_lvl = st.slider("現在のレベル", 0, 3, 3)
    current_clock = st.slider("現在のクロック", 0, 6, 0)
    
    st.header("2. 山札の情報")
    n = st.number_input("山札の残り枚数", 1, 50, 15)
    k = st.number_input("山札内のCX枚数", 0, 8, 3)
    
    st.header("3. 控え室の情報")
    d_total = st.number_input("控え室の総枚数", 0, 50, 10)
    d_cx = st.number_input("控え室のCX枚数", 0, 8, 2)
    
    st.header("4. 自分の状態")
    mem = st.number_input("思い出枚数", 1, 10, 5)
    s1 = st.number_input("1体目ソウル", 1, 5, 2)
    s2 = st.number_input("2体目ソウル", 1, 5, 2)
    s3 = st.number_input("3体目ソウル", 1, 5, 3)

if st.button("勝率を計算する", type="primary"):
    if (k + d_cx) > 8:
        st.error("エラー：CXの合計が8枚を超えています！")
    elif d_cx > d_total:
        st.error("エラー：控え室のCX枚数が総枚数より多いです！")
    else:
        with st.spinner('シミュレート中...'):
            rate = simulate_win_rate_perfect(n, k, d_total, d_cx, [s1, s2, s3], mem, current_lvl, current_clock)
            st.metric(label="勝利確率", value=f"{rate:.1f} %")
            
            if rate > 80:
                st.success("やってみせろよマフヒーなんとでもなるはずだなんとでもなるはずだ。")
            elif rate > 50:
                st.warning("まあ行けるっしょ！")
            else:
                st.error("しゃがめしゃがめしゃがめしゃがめしゃがめしゃがめ。")
