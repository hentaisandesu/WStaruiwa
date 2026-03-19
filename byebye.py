import streamlit as st
import random

# --- 計算用関数 (最新ルール・解決領域・アイヴィ挙動完全準拠版) ---
def simulate_win_rate_perfect(n_deck, k_cx, d_total, d_cx, s_list, mem_count, current_lvl, current_clock, trials=30000):
    wins = 0
    # テキスト通り「思い出の《音楽》キャラの枚数 - 1」
    x_count = max(0, mem_count - 1)
    
    for _ in range(trials):
        # 山札 (1: CX, 0: 通常)
        deck = [1] * k_cx + [0] * (n_deck - k_cx)
        random.shuffle(deck)
        
        # 控え室
        discard_pile = [1] * d_cx + [0] * (d_total - d_cx)
        
        # クロックとレベル
        clock_pile = [0] * current_clock 
        temp_lvl = current_lvl
        is_finished = False

        def add_to_clock(c_pile, d_pile, lvl, card):
            """カードをクロックに置き、レベルアップ判定を行う"""
            c_pile.append(card)
            dead = False
            if len(c_pile) >= 7:
                lvl += 1
                if lvl >= 4:
                    dead = True
                else:
                    # レベル置場には極力「通常札(0)」を置く（プレイング最適化の仮定）
                    if 0 in c_pile:
                        c_pile.remove(0)
                    else:
                        c_pile.pop()
                    # 残りの6枚を控え室へ
                    d_pile.extend(c_pile)
                    c_pile.clear()
            return c_pile, d_pile, lvl, dead

        def trigger_refresh_process(d, discard, c_pile, lvl):
            """リフレッシュとペナルティを1つの解決として割り込ませる(2022年ルール)"""
            # 現在の控え室をシャッフルして新山札へ
            new_deck = discard[:]
            random.shuffle(new_deck)
            discard.clear()
            
            # リフレッシュペナルティ（新しい山札のトップをクロックへ）
            if not new_deck: # 控え室が0枚でリフレッシュした場合（稀なケース）
                return new_deck, discard, c_pile, lvl, False
                
            penalty_card = new_deck.pop()
            c_pile, discard, lvl, dead = add_to_clock(c_pile, discard, lvl, penalty_card)
            return new_deck, discard, c_pile, lvl, dead

        def deal_damage(amount, d, discard, c_pile, lvl):
            """解決領域を介したダメージ処理"""
            resolution_zone = []
            cancel = False
            dead = False
            
            for _ in range(amount):
                # めくる前に山札が空ならリフレッシュ割り込み
                if not d:
                    d, discard, c_pile, lvl, dead = trigger_refresh_process(d, discard, c_pile, lvl)
                    if dead: return d, discard, c_pile, lvl, True
                    if not d: break # リフレッシュしても札がない場合

                card = d.pop()
                resolution_zone.append(card)
                
                # CXが出たらキャンセル確定
                if card == 1:
                    cancel = True
                    break
                    
            if cancel:
                # キャンセル：解決領域のカードをすべて控え室へ
                discard.extend(resolution_zone)
            else:
                # ヒット：解決領域のカードを順番にクロックへ
                for card in resolution_zone:
                    c_pile, discard, lvl, dead = add_to_clock(c_pile, discard, lvl, card)
                    if dead: return d, discard, c_pile, lvl, True
                    
            return d, discard, c_pile, lvl, False

        # --- アタックフェイズ解決 ---
        for s in s_list:
            # ① CXコンボ：1点バーン
            deck, discard_pile, clock_pile, temp_lvl, is_finished = deal_damage(1, deck, discard_pile, clock_pile, temp_lvl)
            if is_finished: break

            # ② CXコンボ：山札削り (1枚ずつ処理し、その都度リフレッシュ判定)
            found_cx = False
            for _ in range(x_count):
                # 削る前に山札がなければリフレッシュ
                if not deck:
                    deck, discard_pile, clock_pile, temp_lvl, is_finished = trigger_refresh_process(deck, discard_pile, clock_pile, temp_lvl)
                    if is_finished: break
                
                # 山札の下から1枚控え室へ
                removed = deck.pop(0) 
                if removed == 1:
                    found_cx = True
                discard_pile.append(removed)
                
                # 削った直後に山札がなくなってもリフレッシュ割り込み
                if not deck:
                    deck, discard_pile, clock_pile, temp_lvl, is_finished = trigger_refresh_process(deck, discard_pile, clock_pile, temp_lvl)
                    if is_finished: break

            if is_finished: break

            # ③ 条件付き1点バーン (削った中にCXがあったなら)
            if found_cx:
                deck, discard_pile, clock_pile, temp_lvl, is_finished = deal_damage(1, deck, discard_pile, clock_pile, temp_lvl)
                if is_finished: break

            # ④ 本体ダメージ
            deck, discard_pile, clock_pile, temp_lvl, is_finished = deal_damage(s, deck, discard_pile, clock_pile, temp_lvl)
            if is_finished: break

        if is_finished:
            wins += 1
            
    return (wins / trials) * 100

# --- Streamlit UI ---
st.set_page_config(page_title="アイヴィ 勝利確率計算機", layout="centered")
st.title("🎴 アイヴィ 勝利確率計算機")
st.caption("最新リフレッシュルール & 解決領域ロジック完全対応版")

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
    mem = st.number_input("思い出の《音楽》キャラ数", 1, 10, 5)
    s_vals = [st.number_input(f"{i+1}体目ソウル", 1, 5, 2 if i < 2 else 3) for i in range(3)]

if st.button("勝率を計算する", type="primary"):
    if (k + d_cx) > 8:
        st.error("エラー：CXの合計が8枚を超えています！")
    elif d_cx > d_total:
        st.error("エラー：控え室のCX枚数が総枚数より多いです！")
    else:
        with st.spinner('30,000回の対戦をシミュレート中...'):
            rate = simulate_win_rate_perfect(n, k, d_total, d_cx, s_vals, mem, current_lvl, current_clock)
            st.metric(label="勝利確率 (LO含む)", value=f"{rate:.2f} %")
            
            if rate > 80:
                st.success("やってみせろよ、なんとでもなるはずだ！")
            elif rate > 50:
                st.warning("まあ、行けるっしょ！")
            else:
                st.error("しゃがめしゃがめしゃがめしゃがめ……")

st.info("※このシミュレーターはアイヴィのCXコンボを3面、かつ全ての「控え室に置く」効果を最大枚数行う前提で計算しています。")
