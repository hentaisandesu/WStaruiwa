import streamlit as st
import random

# --- 計算用関数 (ルール完全準拠版) ---
def simulate_win_rate_perfect(n_deck, k_cx, d_total, d_cx, s_list, mem_count, current_lvl, current_clock, trials=20000):
    wins = 0
    x_count = max(0, mem_count - 1)
    
    for _ in range(trials):
        # 山札と控え室 (1: CX, 0: 通常)
        deck = [1] * k_cx + [0] * (n_deck - k_cx)
        random.shuffle(deck)
        
        discard_pile = [1] * d_cx + [0] * (d_total - d_cx)
        
        # クロック置き場を「枚数」ではなく「カードのリスト」で正確に追跡
        clock_pile = [0] * current_clock 
        temp_lvl = current_lvl
        
        def add_to_clock(c_pile, d_pile, lvl, card):
            """カードをクロックに置き、7枚になったらレベルアップ処理"""
            c_pile.append(card)
            is_dead = False
            if len(c_pile) >= 7:
                lvl += 1
                if lvl >= 4:
                    is_dead = True
                else:
                    # レベル置場には極力「通常札(0)」を置く
                    if 0 in c_pile:
                        c_pile.remove(0)
                    else:
                        c_pile.pop()
                    # 残りの6枚（CXが含まれていればそれも）を控え室へ
                    d_pile.extend(c_pile)
                    c_pile.clear()
            return c_pile, d_pile, lvl, is_dead

        def check_refresh(d, discard, c_pile, lvl):
            """山札が空ならリフレッシュし、新しい山札から1点受ける"""
            is_dead = False
            if not d:
                new_deck = discard[:]
                random.shuffle(new_deck)
                discard.clear()
                # リフレッシュペナルティ（新しい山札のトップをクロックへ）
                if new_deck:
                    penalty_card = new_deck.pop()
                    c_pile, discard, lvl, is_dead = add_to_clock(c_pile, discard, lvl, penalty_card)
                return new_deck, discard, c_pile, lvl, is_dead
            return d, discard, c_pile, lvl, False

        def deal_damage(amount, d, discard, c_pile, lvl):
            """WSのダメージルールを完全再現"""
            is_dead = False
            revealed = []
            cancel = False
            
            for _ in range(amount):
                # めくる前に山札が空ならリフレッシュ
                d, discard, c_pile, lvl, is_dead = check_refresh(d, discard, c_pile, lvl)
                if is_dead: return d, discard, c_pile, lvl, True
                if not d: break

                card = d.pop()
                revealed.append(card)
                
                # CXが出たらその時点でめくるのをやめてキャンセル
                if card == 1:
                    cancel = True
                    break
                    
            if cancel:
                # キャンセル：めくったカードは全て控え室へ
                discard.extend(revealed)
            else:
                # ヒット：めくったカードを順番にクロックへ
                for card in revealed:
                    c_pile, discard, lvl, is_dead = add_to_clock(c_pile, discard, lvl, card)
                    if is_dead: return d, discard, c_pile, lvl, True
                    
            return d, discard, c_pile, lvl, False

        is_finished = False
        for s in s_list:
            if is_finished: break
            
            # ① 1点バーン
            deck, discard_pile, clock_pile, temp_lvl, is_finished = deal_damage(1, deck, discard_pile, clock_pile, temp_lvl)
            if is_finished: break

            # ② 山札削り (思い出-1枚)
            found_cx = False
            for _ in range(x_count):
                deck, discard_pile, clock_pile, temp_lvl, is_finished = check_refresh(deck, discard_pile, clock_pile, temp_lvl)
                if is_finished: break
                if not deck: break
                removed = deck.pop()
                if removed == 1: found_cx = True
                discard_pile.append(removed) # 削ったカードは控え室へ
            
            if is_finished: break

            # ③ 条件付き1点バーン
            if found_cx:
                deck, discard_pile, clock_pile, temp_lvl, is_finished = deal_damage(1, deck, discard_pile, clock_pile, temp_lvl)
            if is_finished: break

            # ④ 本体アタック
            deck, discard_pile, clock_pile, temp_lvl, is_finished = deal_damage(s, deck, discard_pile, clock_pile, temp_lvl)

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
