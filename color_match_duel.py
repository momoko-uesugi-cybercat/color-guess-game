"""
🎨 Color Match Duel — A Two-Player Color Matching Game
Both players see a target color and try to recreate it using a color picker.
The closer match wins the round! 5 rounds, 60 seconds per round.
"""

import streamlit as st
import random
import json
import os
import math
import time
from streamlit_autorefresh import st_autorefresh

# ============================================================
# Page Config
# ============================================================
st.set_page_config(
    page_title="🎨 Color Match Duel",
    page_icon="🎨",
    layout="centered",
)

# ============================================================
# Custom CSS
# ============================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@400;500;600;700;800&display=swap');

    .stApp {
        background: linear-gradient(160deg, #0a0a1a 0%, #1a1a3e 40%, #2a1a4e 100%);
    }

    * {
        font-family: 'Baloo 2', cursive !important;
    }

    h1, h2, h3, p, span, label, div, li {
        color: #ffffff !important;
    }

    .game-title {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #ff6b6b, #ffd93d, #6bcb77, #4d96ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }

    .subtitle {
        text-align: center;
        opacity: 0.5;
        font-size: 1rem;
        margin-top: -8px;
    }

    .color-swatch {
        border-radius: 24px;
        min-height: 140px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.1rem;
        font-weight: 600;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        border: 3px solid rgba(255,255,255,0.1);
        margin: 8px 0;
    }

    .target-swatch {
        border-radius: 28px;
        min-height: 180px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        font-size: 1.3rem;
        font-weight: 700;
        box-shadow: 0 12px 48px rgba(0,0,0,0.4);
        border: 4px solid rgba(255,255,255,0.15);
        margin: 12px 0;
    }

    .score-box {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 16px;
        text-align: center;
        margin: 6px 0;
    }

    .round-badge {
        background: rgba(255,255,255,0.1);
        border-radius: 30px;
        padding: 8px 24px;
        text-align: center;
        display: inline-block;
        font-weight: 600;
        margin: 8px 0;
    }

    .winner-banner {
        background: linear-gradient(135deg, rgba(255,215,0,0.15), rgba(255,165,0,0.1));
        border: 2px solid rgba(255,215,0,0.4);
        border-radius: 20px;
        padding: 24px;
        text-align: center;
        margin: 16px 0;
    }

    .hint-box {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 16px 20px;
        margin: 10px 0;
    }

    .waiting-pulse {
        animation: pulse 2s ease-in-out infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 0.5; }
        50% { opacity: 1; }
    }

    /* Timer styles */
    .timer-container {
        text-align: center;
        margin: 12px 0;
    }

    .timer-text {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: 2px;
    }

    .timer-normal {
        color: #4ade80 !important;
    }

    .timer-warning {
        color: #fbbf24 !important;
    }

    .timer-danger {
        color: #ef4444 !important;
        animation: pulse 0.5s ease-in-out infinite;
    }

    .timer-bar {
        width: 100%;
        height: 8px;
        background: rgba(255,255,255,0.1);
        border-radius: 4px;
        margin-top: 8px;
        overflow: hidden;
    }

    .timer-bar-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 1s linear;
    }

    div[data-testid="stColorPicker"] > div {
        border-radius: 14px;
    }

    div[data-testid="stButton"] > button {
        border-radius: 14px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# Game Constants
# ============================================================
TOTAL_ROUNDS = 5
ROUND_TIME = 60  # seconds per round
GAME_FILE = "/tmp/color_match_duel.json"
DEFAULT_COLOR = "#808080"  # gray — submitted if time runs out

# Target colors
TARGET_COLORS = [
    {"hex": "#e74c3c", "name": "Crimson Red"},
    {"hex": "#3498db", "name": "Ocean Blue"},
    {"hex": "#2ecc71", "name": "Emerald Green"},
    {"hex": "#f39c12", "name": "Amber Gold"},
    {"hex": "#9b59b6", "name": "Royal Purple"},
    {"hex": "#1abc9c", "name": "Turquoise"},
    {"hex": "#e91e63", "name": "Hot Pink"},
    {"hex": "#00bcd4", "name": "Cyan"},
    {"hex": "#ff5722", "name": "Deep Orange"},
    {"hex": "#607d8b", "name": "Steel Blue"},
    {"hex": "#8bc34a", "name": "Lime Green"},
    {"hex": "#ff9800", "name": "Tangerine"},
    {"hex": "#673ab7", "name": "Deep Violet"},
    {"hex": "#009688", "name": "Teal"},
    {"hex": "#c2185b", "name": "Berry"},
    {"hex": "#4caf50", "name": "Forest Green"},
    {"hex": "#2196f3", "name": "Sky Blue"},
    {"hex": "#f44336", "name": "Scarlet"},
    {"hex": "#ffc107", "name": "Sunflower"},
    {"hex": "#795548", "name": "Chocolate"},
]


# ============================================================
# Helper Functions
# ============================================================
def hex_to_rgb(hex_color: str):
    h = hex_color.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def color_distance(hex1: str, hex2: str) -> float:
    r1, g1, b1 = hex_to_rgb(hex1)
    r2, g2, b2 = hex_to_rgb(hex2)
    dr = (r1 - r2) ** 2
    dg = (g1 - g2) ** 2
    db = (b1 - b2) ** 2
    max_dist = math.sqrt(2 * (255**2) + 4 * (255**2) + 3 * (255**2))
    dist = math.sqrt(2 * dr + 4 * dg + 3 * db)
    return round((dist / max_dist) * 100, 1)


def accuracy_score(distance: float) -> int:
    return max(0, round(100 - distance))


def get_text_color(hex_color: str) -> str:
    r, g, b = hex_to_rgb(hex_color)
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    return "#333333" if brightness > 128 else "#ffffff"


def load_game():
    if os.path.exists(GAME_FILE):
        try:
            with open(GAME_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return None


def save_game(state):
    with open(GAME_FILE, "w") as f:
        json.dump(state, f)


def reset_game():
    if os.path.exists(GAME_FILE):
        os.remove(GAME_FILE)
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def init_new_game():
    colors = random.sample(TARGET_COLORS, TOTAL_ROUNDS)
    return {
        "round": 1,
        "targets": [c["hex"] for c in colors],
        "target_names": [c["name"] for c in colors],
        "p1_answers": [],
        "p2_answers": [],
        "p1_score": 0,
        "p2_score": 0,
        "p1_submitted": False,
        "p2_submitted": False,
        "phase": "playing",
        "round_start_time": time.time(),  # <-- timer!
    }


def get_remaining_time(game):
    """Get remaining seconds for this round."""
    start = game.get("round_start_time", time.time())
    elapsed = time.time() - start
    remaining = max(0, ROUND_TIME - elapsed)
    return int(remaining)


def auto_submit_on_timeout(game, player):
    """If time is up and player hasn't submitted, auto-submit default color."""
    answers_key = f"{player}_answers"
    submitted_key = f"{player}_submitted"
    if not game[submitted_key]:
        # Submit whatever color they currently have picked, or default gray
        current_color = st.session_state.get(f"picker_{game['round']}", DEFAULT_COLOR)
        game[answers_key].append(current_color)
        game[submitted_key] = True
    return game


def render_timer(remaining):
    """Display the countdown timer with color coding."""
    minutes = remaining // 60
    seconds = remaining % 60
    time_str = f"{minutes}:{seconds:02d}"

    if remaining > 30:
        css_class = "timer-normal"
        bar_color = "#4ade80"
    elif remaining > 10:
        css_class = "timer-warning"
        bar_color = "#fbbf24"
    else:
        css_class = "timer-danger"
        bar_color = "#ef4444"

    pct = (remaining / ROUND_TIME) * 100

    st.markdown(
        f'<div class="timer-container">'
        f'<span class="timer-text {css_class}">⏱️ {time_str}</span>'
        f'<div class="timer-bar">'
        f'<div class="timer-bar-fill" style="width:{pct}%; background:{bar_color};"></div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# Session State
# ============================================================
if "player" not in st.session_state:
    st.session_state.player = None


# ============================================================
# Title
# ============================================================
st.markdown('<h1 class="game-title">🎨 Color Match Duel</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Match the color. Beat your partner. 💕</p>', unsafe_allow_html=True)
st.markdown("---")


# ============================================================
# Player Selection
# ============================================================
if st.session_state.player is None:
    game = load_game()

    st.markdown("### 👋 Choose your player:")
    st.markdown("")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🌸 Player 1", use_container_width=True):
            st.session_state.player = "p1"
            if game is None:
                save_game(init_new_game())
            st.rerun()

    with col2:
        if st.button("💙 Player 2", use_container_width=True):
            st.session_state.player = "p2"
            if game is None:
                save_game(init_new_game())
            st.rerun()

    st.markdown("")
    st.markdown(
        '<div class="hint-box">'
        "<p>📖 <strong>How to Play:</strong></p>"
        "<p>1️⃣ Both players open the same URL<br>"
        "2️⃣ Choose Player 1 or Player 2<br>"
        "3️⃣ You'll both see a <strong>target color</strong><br>"
        "4️⃣ Use the color picker to match it as closely as you can<br>"
        "5️⃣ You have <strong>60 seconds</strong> per round! ⏱️<br>"
        "6️⃣ After both submit (or time runs out), see who was closer!<br>"
        "7️⃣ <strong>5 rounds</strong> — highest total score wins! 🏆</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("")
    if st.button("🔄 Reset Game", use_container_width=True):
        reset_game()
        st.rerun()

else:
    # ========================================================
    # Main Game
    # ========================================================
    game = load_game()

    if game is None:
        save_game(init_new_game())
        game = load_game()

    # Ensure round_start_time exists (backward compat)
    if "round_start_time" not in game:
        game["round_start_time"] = time.time()
        save_game(game)

    player = st.session_state.player
    player_label = "🌸 Player 1" if player == "p1" else "💙 Player 2"
    other_label = "💙 Player 2" if player == "p1" else "🌸 Player 1"
    submitted_key = f"{player}_submitted"
    other_submitted_key = "p2_submitted" if player == "p1" else "p1_submitted"
    answers_key = f"{player}_answers"

    current_round = game["round"]
    phase = game["phase"]

    # ---- Auto-refresh ONLY during playing phase ----
    if phase == "playing":
        st_autorefresh(interval=1000, key=f"timer_refresh_{current_round}")

    # ---- Check timeout ----
    if phase == "playing":
        remaining = get_remaining_time(game)
        if remaining <= 0:
            # Time's up! Auto-submit for both players
            game = auto_submit_on_timeout(game, "p1")
            game = auto_submit_on_timeout(game, "p2")
            # Calculate scores
            idx = current_round - 1
            target_hex = game["targets"][idx]
            p1_hex = game["p1_answers"][idx]
            p2_hex = game["p2_answers"][idx]
            p1_acc = accuracy_score(color_distance(target_hex, p1_hex))
            p2_acc = accuracy_score(color_distance(target_hex, p2_hex))
            game["p1_score"] += p1_acc
            game["p2_score"] += p2_acc
            game["phase"] = "reveal"
            save_game(game)
            st.rerun()

    # ---- Scoreboard ----
    col_s1, col_s2, col_s3 = st.columns([2, 1, 2])
    with col_s1:
        p1_style = "font-weight:800;" if player == "p1" else "opacity:0.7;"
        st.markdown(
            f'<div class="score-box" style="{p1_style}">'
            f"🌸 Player 1<br><span style='font-size:2rem;'>{game['p1_score']}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with col_s2:
        st.markdown(
            '<div style="text-align:center; padding-top:20px; font-size:1.5rem; opacity:0.3;">vs</div>',
            unsafe_allow_html=True,
        )
    with col_s3:
        p2_style = "font-weight:800;" if player == "p2" else "opacity:0.7;"
        st.markdown(
            f'<div class="score-box" style="{p2_style}">'
            f"💙 Player 2<br><span style='font-size:2rem;'>{game['p2_score']}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown(
        f'<div style="text-align:center; margin:12px 0;">'
        f'<span class="round-badge">Round {min(current_round, TOTAL_ROUNDS)} / {TOTAL_ROUNDS}</span>'
        f"</div>",
        unsafe_allow_html=True,
    )

    # ---- FINAL RESULTS ----
    if phase == "final":
        st.markdown("---")

        p1_total = game["p1_score"]
        p2_total = game["p2_score"]

        if p1_total > p2_total:
            winner = "🌸 Player 1"
        elif p2_total > p1_total:
            winner = "💙 Player 2"
        else:
            winner = None

        if winner:
            st.markdown(
                f'<div class="winner-banner">'
                f'<div style="font-size:3rem;">🏆</div>'
                f"<h2>{winner} wins!</h2>"
                f"<p>Final Score: {p1_total} vs {p2_total}</p>"
                f"</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="winner-banner">'
                '<div style="font-size:3rem;">🤝</div>'
                f"<h2>It's a tie!</h2>"
                f"<p>Both scored {p1_total} — you're a perfect match! 💕</p>"
                "</div>",
                unsafe_allow_html=True,
            )

        st.markdown("### 📊 Round by Round")
        for i in range(TOTAL_ROUNDS):
            target_hex = game["targets"][i]
            target_name = game["target_names"][i]
            p1_hex = game["p1_answers"][i]
            p2_hex = game["p2_answers"][i]
            p1_acc = accuracy_score(color_distance(target_hex, p1_hex))
            p2_acc = accuracy_score(color_distance(target_hex, p2_hex))

            st.markdown(f"**Round {i + 1}: {target_name}**")
            cols = st.columns(3)
            with cols[0]:
                tc = get_text_color(p1_hex)
                st.markdown(
                    f'<div class="color-swatch" style="background:{p1_hex}; color:{tc}; min-height:60px;">'
                    f"🌸 {p1_acc}%</div>",
                    unsafe_allow_html=True,
                )
            with cols[1]:
                tc = get_text_color(target_hex)
                st.markdown(
                    f'<div class="color-swatch" style="background:{target_hex}; color:{tc}; min-height:60px;">'
                    f"🎯</div>",
                    unsafe_allow_html=True,
                )
            with cols[2]:
                tc = get_text_color(p2_hex)
                st.markdown(
                    f'<div class="color-swatch" style="background:{p2_hex}; color:{tc}; min-height:60px;">'
                    f"💙 {p2_acc}%</div>",
                    unsafe_allow_html=True,
                )

        st.balloons()

        st.markdown("---")
        if st.button("🔄 Play Again!", use_container_width=True):
            reset_game()
            st.rerun()

    # ---- REVEAL PHASE ----
    elif phase == "reveal":
        st.markdown("---")
        idx = current_round - 1
        target_hex = game["targets"][idx]
        target_name = game["target_names"][idx]
        p1_hex = game["p1_answers"][idx]
        p2_hex = game["p2_answers"][idx]

        p1_dist = color_distance(target_hex, p1_hex)
        p2_dist = color_distance(target_hex, p2_hex)
        p1_acc = accuracy_score(p1_dist)
        p2_acc = accuracy_score(p2_dist)

        st.markdown(f"### 🎯 Target: {target_name}")
        tc = get_text_color(target_hex)
        st.markdown(
            f'<div class="target-swatch" style="background:{target_hex}; color:{tc};">'
            f"{target_hex}"
            f"</div>",
            unsafe_allow_html=True,
        )

        st.markdown("### Results:")

        col1, col2 = st.columns(2)

        with col1:
            tc = get_text_color(p1_hex)
            st.markdown(
                f'<div class="color-swatch" style="background:{p1_hex}; color:{tc};">'
                f"🌸 Player 1<br>{p1_hex}<br>Accuracy: {p1_acc}%</div>",
                unsafe_allow_html=True,
            )

        with col2:
            tc = get_text_color(p2_hex)
            st.markdown(
                f'<div class="color-swatch" style="background:{p2_hex}; color:{tc};">'
                f"💙 Player 2<br>{p2_hex}<br>Accuracy: {p2_acc}%</div>",
                unsafe_allow_html=True,
            )

        if p1_acc > p2_acc:
            st.success(f"🌸 Player 1 wins this round! ({p1_acc}% vs {p2_acc}%)")
        elif p2_acc > p1_acc:
            st.success(f"💙 Player 2 wins this round! ({p2_acc}% vs {p1_acc}%)")
        else:
            st.info(f"🤝 Perfect tie! Both got {p1_acc}%!")

        st.markdown("")
        if st.button(
            "🏆 See Final Results!" if current_round >= TOTAL_ROUNDS else f"➡️ Next Round (Round {current_round + 1})",
            use_container_width=True,
        ):
            if current_round >= TOTAL_ROUNDS:
                game["phase"] = "final"
            else:
                game["round"] = current_round + 1
                game["p1_submitted"] = False
                game["p2_submitted"] = False
                game["phase"] = "playing"
                game["round_start_time"] = time.time()  # reset timer!
            save_game(game)
            st.rerun()

    # ---- PLAYING PHASE ----
    elif phase == "playing":
        idx = current_round - 1
        target_hex = game["targets"][idx]
        target_name = game["target_names"][idx]
        remaining = get_remaining_time(game)

        st.markdown("---")

        # ⏱️ TIMER
        render_timer(remaining)

        # Show target color
        st.markdown(f"### 🎯 Match this color: *{target_name}*")
        tc = get_text_color(target_hex)
        st.markdown(
            f'<div class="target-swatch" style="background:{target_hex}; color:{tc};">'
            f"Match me!"
            f"</div>",
            unsafe_allow_html=True,
        )

        already_submitted = game[submitted_key]

        if already_submitted:
            my_answer = game[answers_key][idx]
            tc = get_text_color(my_answer)
            st.markdown("### ✅ Your answer:")
            st.markdown(
                f'<div class="color-swatch" style="background:{my_answer}; color:{tc};">'
                f"Your pick: {my_answer}</div>",
                unsafe_allow_html=True,
            )

            if game[other_submitted_key]:
                p1_hex = game["p1_answers"][idx]
                p2_hex = game["p2_answers"][idx]
                p1_acc = accuracy_score(color_distance(target_hex, p1_hex))
                p2_acc = accuracy_score(color_distance(target_hex, p2_hex))
                game["p1_score"] += p1_acc
                game["p2_score"] += p2_acc
                game["phase"] = "reveal"
                save_game(game)
                st.rerun()
            else:
                st.markdown(
                    f'<p class="waiting-pulse" style="text-align:center; font-size:1.1rem; margin-top:20px;">'
                    f"⏳ Waiting for {other_label} to submit...</p>",
                    unsafe_allow_html=True,
                )
        else:
            # Show color picker
            st.markdown(f"### 🖌️ {player_label}, pick your color:")

            chosen_color = st.color_picker(
                "Use the picker to match the target!",
                value="#808080",
                key=f"picker_{current_round}",
            )

            # Preview
            col_preview1, col_preview2 = st.columns(2)
            with col_preview1:
                tc = get_text_color(target_hex)
                st.markdown(
                    f'<div class="color-swatch" style="background:{target_hex}; color:{tc}; min-height:100px;">'
                    f"🎯 Target</div>",
                    unsafe_allow_html=True,
                )
            with col_preview2:
                tc = get_text_color(chosen_color)
                st.markdown(
                    f'<div class="color-swatch" style="background:{chosen_color}; color:{tc}; min-height:100px;">'
                    f"🖌️ Yours</div>",
                    unsafe_allow_html=True,
                )

            st.markdown("")
            if st.button("✅ Lock In My Color!", use_container_width=True):
                game[answers_key].append(chosen_color)
                game[submitted_key] = True

                if game[other_submitted_key]:
                    p1_hex = game["p1_answers"][idx]
                    p2_hex = game["p2_answers"][idx]
                    p1_acc = accuracy_score(color_distance(target_hex, p1_hex))
                    p2_acc = accuracy_score(color_distance(target_hex, p2_hex))
                    game["p1_score"] += p1_acc
                    game["p2_score"] += p2_acc
                    game["phase"] = "reveal"

                save_game(game)
                st.rerun()

    # ---- Footer ----
    st.markdown("---")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        if st.button("🔄 Reset Game", use_container_width=True):
            reset_game()
            st.rerun()
    with col_f2:
        if st.button("🔀 Switch Player", use_container_width=True):
            st.session_state.player = None
            st.rerun()

# ============================================================
# Footer
# ============================================================
st.markdown(
    "<p style='text-align:center; opacity:0.25; font-size:0.8rem; margin-top:20px;'>"
    "🎨 Color Match Duel — Made with love & Streamlit 💕"
    "</p>",
    unsafe_allow_html=True,
)
