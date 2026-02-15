import streamlit as st
import json
import os
import random
import re

# ==========================================
# 1. ฟังก์ชันจัดการข้อมูล
# ==========================================
def load_quiz_data(filename):
    path = os.path.join('modules', filename)
    if not os.path.exists(path): return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except: return []

def get_adaptive_question(pool, level, used_questions):
    available = [q for q in pool if q.get('level') == level and q['question'] not in used_questions]
    if not available: 
        available = [q for q in pool if q['question'] not in used_questions]
    if not available: available = pool

    q = random.choice(available).copy()
    choices = list(q['choices'])
    correct_ans = choices[q['answer_index']]
    random.shuffle(choices)
    q['choices'] = choices
    q['answer_index'] = choices.index(correct_ans)
    return q

# ==========================================
# 2. ตั้งค่าหน้าเว็บ (Fluid UI & Clear Fonts)
# ==========================================
st.set_page_config(page_title="Math Drill Pro", page_icon="📝", layout="wide")

st.markdown("""
    <style>
    .block-container {
        padding: 2rem 1rem !important;
        max-width: 95%;
    }

    h2 { font-size: calc(1.5rem + 1vw) !important; font-weight: 700; }
    h3 { font-size: calc(1.1rem + 0.5vw) !important; line-height: 1.4 !important; }

    /* ปุ่มคำตอบ: หนา ชัด เข้ม (v2.1) */
    .stButton button {
        width: 100%;
        white-space: normal !important;
        height: auto !important;
        min-height: 3.5rem;
        font-size: 1.2rem !important;
        font-weight: 700 !important;
        color: #1a237e !important;
        border: 2px solid #e0e0e0 !important;
        background-color: #ffffff !important;
        margin-bottom: 0.5rem;
    }
    
    .stButton button:hover {
        border-color: #007bff !important;
        background-color: #f0f7ff !important;
    }

    /* กล่องขั้นตอนการคิด (v2.3: ป้องกันการแตกของตัวเลขทศนิยม) */
    .explanation-container {
        background-color: #f8f9fa;
        border-left: 5px solid #007bff;
        padding: 1.2rem;
        border-radius: 8px;
        font-size: 1.1rem;
        line-height: 1.6;
        color: #333;
    }
    .exp-step {
        display: block;
        margin-bottom: 0.6rem;
        word-wrap: break-word;
    }
    
    @media (max-width: 640px) {
        .block-container { padding: 1rem 0.5rem !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# จัดการ State
if 'quiz_active' not in st.session_state: st.session_state.quiz_active = False
if 'step' not in st.session_state: st.session_state.step = 1
if 'history' not in st.session_state: st.session_state.history = [] 
if 'used_questions' not in st.session_state: st.session_state.used_questions = []
if 'level' not in st.session_state: st.session_state.level = 1
if 'current_q' not in st.session_state: st.session_state.current_q = None
if 'answered' not in st.session_state: st.session_state.answered = False

# ==========================================
# 3. Sidebar
# ==========================================
with st.sidebar:
    st.title("📚 คลังข้อสอบ")
    if os.path.exists('modules'):
        files = sorted([f for f in os.listdir('modules') if f.endswith('.json')])
        selected_file = st.selectbox("เลือกบทเรียน", files)
        
        if st.button("🔄 เริ่มต้นใหม่", type="primary", use_container_width=True):
            full_pool = load_quiz_data(selected_file)
            if full_pool:
                st.session_state.pool = full_pool
                st.session_state.quiz_active = True
                st.session_state.step = 1
                st.session_state.history = []
                st.session_state.used_questions = []
                st.session_state.level = 1
                st.session_state.answered = False
                
                first_q = get_adaptive_question(full_pool, 1, [])
                st.session_state.current_q = first_q
                st.session_state.used_questions.append(first_q['question'])
                st.rerun()

    if st.session_state.quiz_active:
        st.write("---")
        score = sum(item.get('คะแนนที่ได้', 0) for item in st.session_state.history)
        st.write(f"คะแนนปัจจุบัน: **{score}**")
        if st.session_state.step <= 10:
            st.progress(st.session_state.step / 10)
            st.caption(f"ข้อที่ {st.session_state.step} จาก 10")

# ==========================================
# 4. Main UI
# ==========================================
if st.session_state.quiz_active:
    if st.session_state.step <= 10:
        q = st.session_state.current_q
        
        st.markdown(f"## ข้อที่ {st.session_state.step} / 10")
        
        # แสดงแค่ดาว (v2.1)
        stars = "⭐" * st.session_state.level
        st.write(f"ระดับความยาก: {stars}")
        
        # โจทย์
        clean_q = q['question'].replace('$', '')
        st.markdown(f"""<div style="background-color: #e1f5fe; padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem; border: 1px solid #b3e5fc;">
            <h3 style="margin:0; color: #01579b;">{clean_q}</h3>
        </div>""", unsafe_allow_html=True)
        
        # ปุ่มคำตอบ
        cols = st.columns(2)
        for i, choice in enumerate(q['choices']):
            clean_choice = str(choice).replace('$', '')
            with cols[i%2]:
                if st.button(clean_choice, key=f"ans_{i}", use_container_width=True, disabled=st.session_state.answered):
                    st.session_state.answered = True
                    is_correct = (i == q['answer_index'])
                    st.session_state.history.append({
                        "ข้อ": st.session_state.step,
                        "ดาว": st.session_state.level,
                        "ผล": "✅" if is_correct else "❌",
                        "คะแนนที่ได้": st.session_state.level if is_correct else 0
                    })
                    st.session_state.last_res = is_correct
                    st.rerun()

        if st.session_state.answered:
            if st.session_state.last_res:
                st.success("ถูกต้อง!")
            else:
                ans_text = str(q['choices'][q['answer_index']]).replace('$', '')
                st.error(f"ผิดครับ... คำตอบที่ถูกต้องคือ: {ans_text}")
            
            # --- แก้ไขระบบแสดงผลขั้นตอนการคิด (v2.3: ป้องกันทศนิยมแตกบรรทัด) ---
            st.markdown("### 💡 ขั้นตอนการคิด:")
            exp_text = q['explanation'].replace('$', '')
            
            # ใช้ regex หา "ตัวเลขข้อ" (เช่น 1. หรือ 2.) ที่ตามด้วยช่องว่าง 
            # และต้องไม่ใช่ตัวเลขที่อยู่ติดกับจุดทศนิยมแบบไม่มีช่องว่าง
            parts = re.split(r'(\d\.\s)', exp_text)
            
            if len(parts) > 1:
                html_content = ""
                # ล้างส่วนเกินที่อาจเกิดจากการ split
                current_text = parts[0].strip()
                if current_text:
                    html_content += f'<div class="exp-step">{current_text}</div>'
                
                for j in range(1, len(parts), 2):
                    num_label = parts[j].strip()
                    main_text = parts[j+1].strip() if j+1 < len(parts) else ""
                    html_content += f'<div class="exp-step"><b>{num_label}</b> {main_text}</div>'
                
                st.markdown(f'<div class="explanation-container">{html_content}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="explanation-container">{exp_text}</div>', unsafe_allow_html=True)
            # -----------------------------------------------------------
            
            st.write("")
            if st.button("ไปยังข้อถัดไป ➡️", type="primary", use_container_width=True):
                if st.session_state.last_res:
                    if st.session_state.level < 3: st.session_state.level += 1
                else:
                    if st.session_state.level > 1: st.session_state.level -= 1
                
                st.session_state.step += 1
                if st.session_state.step <= 10:
                    new_q = get_adaptive_question(st.session_state.pool, st.session_state.level, st.session_state.used_questions)
                    st.session_state.current_q = new_q
                    st.session_state.used_questions.append(new_q['question'])
                st.session_state.answered = False
                st.rerun()
    else:
        st.balloons()
        st.header("🏁 สรุปผลการทดสอบ")
        total = sum(item.get('คะแนนที่ได้', 0) for item in st.session_state.history)
        st.metric("คะแนนรวมทั้งหมด", f"{total} แต้ม")
        st.dataframe(st.session_state.history, use_container_width=True)
        if st.button("ทำใหม่อีกครั้ง", type="primary", use_container_width=True):
            st.session_state.quiz_active = False
            st.rerun()
else:
    st.title("🌟 Math Drill")
    st.write("เลือกบทเรียนที่แถบข้างเพื่อเริ่มทำแบบฝึกหัด")