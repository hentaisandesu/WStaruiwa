import streamlit as st
import random

def simulate_win_rate_perfect(n_deck, k_cx, d_total, d_cx, s_list, mem_count, current_lvl, current_clock, trials=30000):
    wins = 0
    x_count = max(0, mem_count - 1)
    
    for _ in range(trials):
        deck = [1] * k_cx + [0] * (n_deck - k_cx)
        random.shuffle(deck)
        
        discard_pile = [1] * d_cx + [0] * (d_total - d_cx)
        clock_pile = [0] * current_clock 
        temp_lvl = current_lvl
        is_finished = False

        def add_to_clock(c_pile, d_pile, lvl, card):
            c_pile.append(card)
            dead = False
            if len(c_pile) >= 7:
                lvl += 1
                if lvl >= 4:
                    dead = True
                else:
                    c_pile.pop() 
                    d_pile.extend(c_pile)
                    c_pile.clear()
            return c_pile, d_pile, lvl, dead

        def trigger_refresh_process(d, discard, c_pile, lvl):
            new_deck = discard[:]
            random.shuffle(new_deck)
            discard.clear()
            
            if not new_deck: 
                return new_deck, discard, c_pile, lvl, False
                
            penalty_card = new_deck.pop()
            c_pile, discard, lvl, dead = add_to_clock(c_pile, discard, lvl, penalty_card)
            return new_deck, discard, c_pile, lvl, dead

        def deal_damage(amount, d, discard, c_pile, lvl):
            resolution_zone = []
            cancel = False
            dead = False
            
            for _ in range(amount):
                if not d:
                    d, discard, c_pile, lvl, dead = trigger_refresh_process(d, discard, c_pile, lvl)
                    if dead: return d, discard, c_pile, lvl, True
                    if not d: break 

                card = d.pop()
                resolution_zone.append(card)
                
                # 【修正の核心】めくった直後、山札が0になった瞬間にリフレッシュを割り込ませる
                if not d:
                    d, discard, c_pile, lvl, dead = trigger_refresh_process(d, discard, c_pile, lvl)
                    if dead: return d, discard, c_pile, lvl, True
                
                if card == 1:
                    cancel = True
                    break
                    
            if cancel:
                discard.extend(resolution_zone)
            else:
                for card in resolution_zone:
                    c_pile, discard, lvl, dead = add_to_clock(c_pile, discard, lvl, card)
                    if dead: return d, discard, c_pile, lvl, True
                    
            return d, discard, c_pile, lvl, False

        # --- アタックフェイズ解決 ---
        for s in s_list:
            deck, discard_pile, clock_pile, temp_lvl, is_finished = deal_damage(1, deck, discard_pile, clock_pile, temp_lvl)
            if is_finished: break

            found_cx = False
            for _ in range(x_count):
                if not deck:
                    deck, discard_pile, clock_pile, temp_lvl, is_finished = trigger_refresh_process(deck, discard_pile, clock_pile, temp_lvl)
                    if is_finished: break
                
                removed = deck.pop(0) 
                if removed == 1:
                    found_cx = True
                discard_pile.append(removed)
                
                if not deck:
                    deck, discard_pile, clock_pile, temp_lvl, is_finished = trigger_refresh_process(deck, discard_pile, clock_pile, temp_lvl)
                    if is_finished: break

            if is_finished: break

            if found_cx:
                deck, discard_pile, clock_pile, temp_lvl, is_finished = deal_damage(1, deck, discard_pile, clock_pile, temp_lvl)
                if is_finished: break

            deck, discard_pile, clock_pile, temp_lvl, is_finished = deal_damage(s, deck, discard_pile, clock_pile, temp_lvl)
            if is_finished: break

        if is_finished:
            wins += 1
            
    return (wins / trials) * 100

# --- Streamlit UI ---
st.set_page_config(page_title="アイヴィ 勝利確率計算機", layout="centered")
st.title("🎴 アイヴィ 勝利確率計算機")
st.caption("連動は任意効果ですが、全て使う想定で計算します")

with st.sidebar:
    st.header("1. 相手の状態")
    current_lvl = st.slider("現在のレベル", 0, 3, 3)
    current_clock = st.slider("現在のクロック", 0, 6, 1) # デフォルトを1にしました
    
    st.header("2. 山札の情報")
    n = st.number_input("山札の残り枚数", 1, 50, 1)
    k = st.number_input("山札内のCX枚数", 0, 8, 1)
    
    st.header("3. 控え室の情報")
    d_total = st.number_input("控え室の総枚数", 0, 50, 20)
    d_cx = st.number_input("控え室のCX枚数", 0, 8, 0)
    
    st.header("4. 自分の状態")
    mem = st.number_input("思い出の《音楽》キャラ数", 1, 10, 1)
    s_vals = [st.number_input(f"{i+1}体目ソウル", 1, 5, 1) for i in range(3)]

if st.button("勝率を計算する", type="primary"):
    if (k + d_cx) > 8:
        st.error("エラー：CXの合計が8枚を超えています！")
    elif d_cx > d_total:
        st.error("エラー：控え室のCX枚数が総枚数より多いです！")
    else:
        with st.spinner('30,000回の対戦をシミュレート中...'):
            rate = simulate_win_rate_perfect(n, k, d_total, d_cx, s_vals, mem, current_lvl, current_clock)
            st.metric(label="勝利確率", value=f"{rate:.2f} %")
            
            if rate == 100.00:
                st.success("GG！")
            elif rate > 80:
                st.success("なんとでもなるはずだ！")
            elif rate > 50:
                st.warning("五分以上！")
            else:
                st.error("しゃがむ？")
