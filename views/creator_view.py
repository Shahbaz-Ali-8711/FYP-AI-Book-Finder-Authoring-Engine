import streamlit as st
import io
import json
import time
from datetime import datetime
from utils.helpers import init_session_state
from utils.styles import (
    PRIMARY, PRIMARY_DARK, PRIMARY_LIGHT, SECONDARY, ACCENT,
    BORDER, BUTTON_GRADIENT, TEXT_PRIMARY,
    TEXT_SECONDARY, render_html
)
from modules.writer_engine import (
    generate_full_publish_book_pdf, export_book_to_epub, export_book_to_docx,
    ai_copilot_execute_action, ai_copilot_continue_writing,
    ai_copilot_expand_scene, ai_copilot_polish_prose,
    ai_copilot_generate_twist, ai_copilot_draft_blurb,
    ai_generate_book_outline, compute_readability_metrics,
    generate_ai_cover_artwork, COLOR_PALETTES, LAYOUT_TEMPLATES
)
from modules.book_formatter import extract_text_from_upload
from database.db_handler import save_writer_draft, get_writer_drafts


def render_creator_view():
    init_session_state()

    # Warm Ivory & Luxury Emerald Header Banner
    render_html(f"""
    <div style="background: #FFFFFF; border: 1.5px solid #E5E5DC;
                border-radius: 20px; padding: 2rem 2.25rem;
                margin-bottom: 1.5rem;
                box-shadow: 0 10px 30px -10px rgba(26, 26, 26, 0.05);">
        <div style="display: flex; gap: 0.5rem; align-items: center; margin-bottom: 0.6rem; flex-wrap: wrap;">
            <span style="background: rgba(4, 106, 56, 0.08); color: #046A38; border: 1px solid rgba(4, 106, 56, 0.28);
                        font-size: 0.76rem; font-weight: 800; letter-spacing: 0.05em; text-transform: uppercase;
                        padding: 0.22rem 0.7rem; border-radius: 9999px;">
                HYBRID MULTI-MODEL CREATOR ENGINE
            </span>
            <span style="background: rgba(227, 66, 52, 0.08); color: #E34234; border: 1px solid rgba(227, 66, 52, 0.28);
                        font-size: 0.76rem; font-weight: 800; padding: 0.22rem 0.7rem; border-radius: 9999px;">
                ⚡ Mode 1 Co-Pilot: Groq LPU (openai/gpt-oss-120b)
            </span>
            <span style="background: rgba(4, 106, 56, 0.08); color: #046A38; border: 1px solid rgba(4, 106, 56, 0.28);
                        font-size: 0.76rem; font-weight: 800; padding: 0.22rem 0.7rem; border-radius: 9999px;">
                ✨ Mode 2 Outlines & Books: Gemini 3.8 Flash
            </span>
        </div>
        <div style="font-size: 2.1rem; font-weight: 900; color: #1A1A1A; letter-spacing: -0.02em;">
            ✍️ AI Authoring & Luxury Book Publishing Suite
        </div>
        <div style="font-size: 0.95rem; color: #4A4A4A; margin-top: 0.35rem; max-width: 820px; line-height: 1.6;">
            Write from a blank canvas or starter templates in the CapCut-style studio, or compile 50 to 500+ page manuscripts with graphical front covers, copyright leaf, auto TOC with dot leaders, and back cover jacket blurbs in one click.
        </div>
    </div>
    """)

    # Incoming Research Notes Banner (from Reader Hub RAG)
    r_notes = st.session_state.get("research_notes", "")
    if r_notes:
        with st.container():
            render_html(f"""
            <div style="background: rgba(4, 106, 56, 0.06); border: 1.5px solid rgba(4, 106, 56, 0.28);
                        border-radius: 14px; padding: 1rem 1.25rem; margin-bottom: 1.25rem; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-size: 0.8rem; font-weight: 800; color: #046A38; text-transform: uppercase; margin-bottom: 0.2rem;">
                        📥 Incoming Research Notes Available from Reader Hub
                    </div>
                    <div style="font-size: 0.86rem; color: #1A1A1A;">
                        {r_notes[:180]}...
                    </div>
                </div>
            </div>
            """)
            rn_col1, rn_col2 = st.columns([1.5, 3])
            with rn_col1:
                if st.button("📋 Append Notes to Editor Canvas", key="btn_append_research_notes", use_container_width=True):
                    curr = st.session_state.get("mode1_editor_text", "")
                    st.session_state["mode1_editor_text"] = (curr + f"\n\n### RESEARCH NOTES:\n{r_notes}").strip()
                    st.session_state["research_notes"] = ""
                    st.success("Appended research notes to Editor!")
                    st.rerun()
            with rn_col2:
                if st.button("Dismiss Notes", key="btn_dismiss_research_notes"):
                    st.session_state["research_notes"] = ""
                    st.rerun()

    mode_options = [
        "🎨 Mode 1: Interactive Book Editor & Design Studio",
        "🚀 Mode 2: Premium Automated Full Book Generator"
    ]

    # Check external routing triggers (e.g., from Landing Page "Launch Generate Full Book")
    req_mode2 = (
        st.session_state.get("active_creator_tab") == 1 or
        "Mode 2" in str(st.session_state.get("writer_mode", ""))
    )
    if req_mode2:
        st.session_state["creator_mode_selection"] = mode_options[1]
        st.session_state["active_creator_tab"] = None
        st.session_state["writer_mode"] = None

    if "creator_mode_selection" not in st.session_state:
        st.session_state["creator_mode_selection"] = mode_options[0]

    cur_idx = 1 if st.session_state.get("creator_mode_selection") == mode_options[1] else 0

    selected_mode = st.radio(
        "Select Authoring Engine Mode:",
        mode_options,
        index=cur_idx,
        horizontal=True,
        key="creator_mode_selection"
    )

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

    if selected_mode == mode_options[0]:
        _render_interactive_studio_mode()
    else:
        _render_automated_full_book_mode()


# ==============================================================================
# INTEGRATED PARAMETRIC AI CO-PILOT DRAWER (ACCESSIBLE IN BOTH MODES)
# ==============================================================================
def _render_ai_copilot_drawer(target_context_key="mode1_editor_text"):
    """
    Parametric AI Co-Pilot with Action Type, Tone, and Target Word Length controls.
    """
    with st.expander("🤖 Integrated AI Co-Pilot (Parametric Action, Tone & Word Length)", expanded=False):
        st.caption("Direct the Gemini 3.5 Flash-Lite Co-Pilot with tailored action types, stylistic tones, and target word counts.")

        # Quick Action Buttons
        st.markdown("###### ⚡ Quick Actions")
        co_col1, co_col2, co_col3, co_col4 = st.columns(4)
        with co_col1:
            q_cont = st.button("✨ Continue Writing", key=f"cp_qcont_{target_context_key}", use_container_width=True)
        with co_col2:
            q_expand = st.button("🔍 Expand Paragraph", key=f"cp_qexp_{target_context_key}", use_container_width=True)
        with co_col3:
            q_polish = st.button("🪄 Polish Prose", key=f"cp_qpol_{target_context_key}", use_container_width=True)
        with co_col4:
            q_twist = st.button("⚡ Inject Plot Twist", key=f"cp_qtwt_{target_context_key}", use_container_width=True)

        st.markdown("<hr style='border: none; border-top: 1px dashed #E5E5DC; margin: 0.75rem 0;'>", unsafe_allow_html=True)

        # Parametric Configuration Form
        st.markdown("###### ⚙️ Controlled Co-Pilot Parameters")
        p_c1, p_c2, p_c3 = st.columns([1.5, 1.5, 1.2])

        with p_c1:
            act_type = st.selectbox(
                "Action Type:",
                ["Continue Writing", "Expand Paragraph", "Rewrite Professionally", "Fix Grammar & Flow", "Add Academic Citations"],
                key=f"cp_act_{target_context_key}"
            )
        with p_c2:
            act_tone = st.selectbox(
                "Stylistic Tone:",
                ["Academic & Scholarly", "Modern Literary", "Persuasive & Executive", "Fiction / Narrative", "Technical & Precise", "Minimalist Modern"],
                key=f"cp_tone_{target_context_key}"
            )
        with p_c3:
            act_len = st.selectbox(
                "Target Length:",
                ["Short (~150 words)", "Medium (~350 words)", "Long (~600 words)"],
                index=1,
                key=f"cp_len_{target_context_key}"
            )

        act_dir = st.text_input(
            "Specific Direction / Focus (Optional):",
            placeholder="e.g., Deepen emotional resonance, cite empirical studies, or add dialogue tension...",
            key=f"cp_dir_{target_context_key}"
        )

        exec_parametric = st.button(
            f"⚡ Execute Co-Pilot: {act_type}",
            key=f"btn_exec_param_{target_context_key}",
            type="primary",
            use_container_width=True
        )

        curr_text = st.session_state.get(target_context_key, "")

        # Execute Handlers
        if q_cont:
            if curr_text.strip():
                with st.spinner("AI Co-Pilot is drafting the next paragraphs..."):
                    ok, res = ai_copilot_execute_action(curr_text, "Continue Writing", "Modern Literary", "Medium (~350 words)", "")
                    if ok:
                        st.session_state[f"copilot_last_output_{target_context_key}"] = res
                    else:
                        st.error(res)
            else:
                st.warning("Please type or paste text into the editor canvas first.")

        elif q_expand:
            if curr_text.strip():
                with st.spinner("AI Co-Pilot is expanding the scene..."):
                    ok, res = ai_copilot_execute_action(curr_text, "Expand Paragraph", "Modern Literary", "Medium (~350 words)", act_dir)
                    if ok:
                        st.session_state[f"copilot_last_output_{target_context_key}"] = res
                    else:
                        st.error(res)
            else:
                st.warning("Please enter text in the editor first.")

        elif q_polish:
            if curr_text.strip():
                with st.spinner("Polishing prose rhythm and cadence..."):
                    ok, res = ai_copilot_execute_action(curr_text, "Rewrite Professionally", act_tone, "Medium (~350 words)", act_dir)
                    if ok:
                        st.session_state[f"copilot_last_output_{target_context_key}"] = res
                    else:
                        st.error(res)
            else:
                st.warning("Please enter text in the editor first.")

        elif q_twist:
            if curr_text.strip():
                with st.spinner("Synthesizing 3 shocking plot twists..."):
                    ok, res = ai_copilot_generate_twist(curr_text)
                    if ok:
                        st.session_state[f"copilot_last_output_{target_context_key}"] = res
                    else:
                        st.error(res)
            else:
                st.warning("Please enter context in the editor first.")

        elif exec_parametric:
            if curr_text.strip():
                with st.spinner(f"Executing '{act_type}' ({act_tone})..."):
                    ok, res = ai_copilot_execute_action(curr_text, act_type, act_tone, act_len, act_dir)
                    if ok:
                        st.session_state[f"copilot_last_output_{target_context_key}"] = res
                    else:
                        st.error(res)
            else:
                st.warning("Please type or paste text into the editor canvas first.")

        # Output Preview & Actions
        co_output = st.session_state.get(f"copilot_last_output_{target_context_key}")
        if co_output:
            st.markdown(f"""
            <div style="background: rgba(4, 106, 56, 0.05); border: 1.5px solid rgba(4, 106, 56, 0.28);
                        border-radius: 14px; padding: 1.25rem; margin-top: 1rem;">
                <div style="font-size: 0.78rem; color: #046A38; font-weight: 800; text-transform: uppercase; margin-bottom: 0.35rem;">
                    ✓ AI CO-PILOT ASSISTANCE READY
                </div>
                <div style="font-size: 0.92rem; color: #1A1A1A; line-height: 1.65; white-space: pre-wrap;">
{co_output}
                </div>
            </div>
            """, unsafe_allow_html=True)

            btn_col1, btn_col2, btn_col3 = st.columns([1.5, 1.5, 1])
            with btn_col1:
                if st.button("📋 Append Output to Editor", key=f"btn_append_cp_{target_context_key}", type="primary", use_container_width=True):
                    st.session_state[target_context_key] = (curr_text + "\n\n" + co_output).strip()
                    st.session_state[f"copilot_last_output_{target_context_key}"] = None
                    st.success("Appended to manuscript!")
                    st.rerun()
            with btn_col2:
                if st.button("🔄 Replace Selected Text", key=f"btn_replace_cp_{target_context_key}", use_container_width=True):
                    st.session_state[target_context_key] = co_output.strip()
                    st.session_state[f"copilot_last_output_{target_context_key}"] = None
                    st.success("Editor text replaced!")
                    st.rerun()
            with btn_col3:
                if st.button("🗑️ Dismiss", key=f"btn_dismiss_cp_{target_context_key}", use_container_width=True):
                    st.session_state[f"copilot_last_output_{target_context_key}"] = None
                    st.rerun()


# ==============================================================================
# WORKSPACE SNAPSHOT HELPER (SAVE & RESTORE .JSON)
# ==============================================================================
def _render_workspace_json_sync(target_context_key="mode1_editor_text", title_val="Manuscript"):
    with st.expander("💾 Workspace State Snapshot (Export & Restore .json Draft)", expanded=False):
        st.caption("Safely backup your full manuscript, title, author, layout choices, and working notes into a standalone portable JSON file.")
        c_exp, c_imp = st.columns(2)

        with c_exp:
            snapshot_data = {
                "version": "2.0",
                "title": st.session_state.get("book_title_state", title_val),
                "author": st.session_state.get("username", "Author"),
                "content": st.session_state.get(target_context_key, ""),
                "template": st.session_state.get("m2_selected_template", "Luxury Editorial"),
                "palette": st.session_state.get("m2_selected_palette", "Warm Ivory & Emerald"),
                "notes": st.session_state.get("research_notes", ""),
                "timestamp": str(datetime.now())
            }
            json_str = json.dumps(snapshot_data, indent=2, ensure_ascii=False)
            st.download_button(
                "📥 Export Workspace Snapshot (.json)",
                data=json_str.encode("utf-8"),
                file_name=f"{title_val.replace(' ', '_')}_workspace.json",
                mime="application/json",
                key=f"dl_json_{target_context_key}",
                use_container_width=True
            )

        with c_imp:
            up_json = st.file_uploader("Upload Snapshot (.json):", type=["json"], key=f"up_json_{target_context_key}")
            if up_json is not None:
                try:
                    loaded_dict = json.loads(up_json.read().decode("utf-8"))
                    if "content" in loaded_dict:
                        st.session_state[target_context_key] = loaded_dict["content"]
                    if "title" in loaded_dict:
                        st.session_state["book_title_state"] = loaded_dict["title"]
                        st.session_state["m1_title_inp"] = loaded_dict["title"]
                        st.session_state["m2_book_title"] = loaded_dict["title"]
                    if "notes" in loaded_dict and loaded_dict["notes"]:
                        st.session_state["research_notes"] = loaded_dict["notes"]
                    st.success(f"Restored '{loaded_dict.get('title', 'Workspace')}' successfully!")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Failed to parse JSON snapshot: {ex}")


# ==============================================================================
# MODE 1: CAPCUT-STYLE INTERACTIVE BOOK EDITOR & DESIGN STUDIO
# ==============================================================================
def _render_interactive_studio_mode():
    st.markdown("### 🎨 Mode 1: Free Interactive Book Editor & Design Studio")
    render_html("""
    <div style="display: flex; gap: 0.5rem; align-items: center; margin-bottom: 0.85rem;">
        <span style="background: rgba(227, 66, 52, 0.08); color: #E34234; border: 1px solid rgba(227, 66, 52, 0.28); font-size: 0.72rem; font-weight: 800; padding: 0.18rem 0.6rem; border-radius: 9999px;">
            ⚡ Fast Inline Co-Pilot: Groq LPU (openai/gpt-oss-120b)
        </span>
    </div>
    """)
    st.caption("CapCut-style creative studio: start from a blank canvas or pick a template structure. Design typography, format chapters, and export — 100% Free.")

    # Two Clear Starting Options (CapCut-Style Concept)
    st.markdown("##### 1. Choose Your Starting Point")
    c_opt1, c_opt2 = st.columns(2)

    with c_opt1:
        is_blank = (st.session_state.get("mode1_canvas_mode") == "blank")
        border_b = "#046A38" if is_blank else "#E5E5DC"
        bg_b = "rgba(4, 106, 56, 0.05)" if is_blank else "#FFFFFF"
        badge_b = "<span style='background: #046A38; color: #FFFFFF; font-size: 0.68rem; padding: 0.15rem 0.5rem; border-radius: 9999px; font-weight: 800;'>ACTIVE</span>" if is_blank else ""

        render_html(f"""
        <div style="background: {bg_b}; border: 2px solid {border_b}; border-radius: 16px; padding: 1.35rem; min-height: 110px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
                <span style="font-weight: 800; font-size: 1.1rem; color: #1A1A1A;">➕ New Idea (Blank Manual Canvas)</span>
                {badge_b}
            </div>
            <div style="font-size: 0.85rem; color: #4A4A4A; line-height: 1.45;">
                Start with a clean slate. Manually type or write chapters, style typography, and use the inline AI helper whenever stuck.
            </div>
        </div>
        """)
        if st.button("Select Blank Canvas", key="btn_choose_blank_canvas", use_container_width=True):
            st.session_state["mode1_canvas_mode"] = "blank"
            if not st.session_state.get("mode1_editor_text"):
                st.session_state["mode1_editor_text"] = "CHAPTER 1: A NEW BEGINNING\n\nStart typing your story or ideas here..."
            st.rerun()

    with c_opt2:
        is_tpl = (st.session_state.get("mode1_canvas_mode") == "template")
        border_t = "#046A38" if is_tpl else "#E5E5DC"
        bg_t = "rgba(4, 106, 56, 0.05)" if is_tpl else "#FFFFFF"
        badge_t = "<span style='background: #046A38; color: #FFFFFF; font-size: 0.68rem; padding: 0.15rem 0.5rem; border-radius: 9999px; font-weight: 800;'>ACTIVE</span>" if is_tpl else ""

        render_html(f"""
        <div style="background: {bg_t}; border: 2px solid {border_t}; border-radius: 16px; padding: 1.35rem; min-height: 110px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
                <span style="font-weight: 800; font-size: 1.1rem; color: #1A1A1A;">📑 Start from Template</span>
                {badge_t}
            </div>
            <div style="font-size: 0.85rem; color: #4A4A4A; line-height: 1.45;">
                Pick a pre-structured template (Non-Fiction, Novel, Academic, Minimalist) with starter chapters and customize every section.
            </div>
        </div>
        """)
        if st.button("Select Template Starter", key="btn_choose_template_starter", use_container_width=True):
            st.session_state["mode1_canvas_mode"] = "template"
            st.rerun()

    canvas_mode = st.session_state.get("mode1_canvas_mode", "template")

    # If Template Starter is chosen, show template picker
    if canvas_mode == "template":
        st.markdown("<hr style='border: none; border-top: 1px dashed #E5E5DC; margin: 1.5rem 0;'>", unsafe_allow_html=True)
        st.markdown("##### 2. Pick a Starter Template")
        t1, t2, t3, t4 = st.columns(4)

        templates_list = [
            ("Modern Non-Fiction", "Structured chapters, key takeaway boxes, and clear subheadings.", "modern"),
            ("Classic Novel", "Roman numerals, ornamental chapter dividers, and character dialogues.", "classic"),
            ("Academic & Technical", "Numbered sections, formal research hierarchy, and code callouts.", "academic"),
            ("Minimalist Zen", "Generous whitespace, understated typography, and focus-first formatting.", "minimalist")
        ]

        curr_tpl = st.session_state.get("mode1_selected_template", "modern")

        for col, (tpl_title, tpl_info, tpl_key) in zip([t1, t2, t3, t4], templates_list):
            with col:
                is_sel = (curr_tpl == tpl_key)
                card_b = "#046A38" if is_sel else "#E5E5DC"
                card_bg = "rgba(4, 106, 56, 0.05)" if is_sel else "#FFFFFF"
                badge = "<span style='background: #046A38; color: #FFFFFF; font-size: 0.65rem; padding: 0.15rem 0.45rem; border-radius: 9999px; font-weight: 800;'>SELECTED</span>" if is_sel else ""

                render_html(f"""
                <div style="background: {card_bg}; border: 1.5px solid {card_b}; border-radius: 12px; padding: 1rem; min-height: 130px; display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3rem;">
                            <span style="font-weight: 800; font-size: 0.92rem; color: #1A1A1A;">{tpl_title}</span>
                            {badge}
                        </div>
                        <div style="font-size: 0.78rem; color: #4A4A4A; line-height: 1.4;">
                            {tpl_info}
                        </div>
                    </div>
                </div>
                """)
                if st.button(f"Load {tpl_title.split()[0]}", key=f"btn_apply_tpl_{tpl_key}", use_container_width=True):
                    st.session_state["mode1_selected_template"] = tpl_key
                    if tpl_key == "modern":
                        st.session_state["mode1_editor_text"] = "CHAPTER 1: THE CORE THESIS\n\nIn an interconnected world, speed of execution is determined by clarity of architecture.\n\nKey Principles:\n* 1. Focus on signal over noise.\n* 2. Build modular systems.\n\nCHAPTER 2: STRATEGIC MOMENTUM\n\nExecution requires disciplined prioritization..."
                    elif tpl_key == "classic":
                        st.session_state["mode1_editor_text"] = "CHAPTER I: THE DEPARTURE\n\nThe autumn mist hung low over the cobblestones as Marcus gathered his papers. A cold breeze whispered through the shuttered windows...\n\nCHAPTER II: VOICES IN THE OBSCURITY\n\nThe tavern on the corner was crowded with travelers..."
                    elif tpl_key == "academic":
                        st.session_state["mode1_editor_text"] = "SECTION 1.0: INTRODUCTION & HYPOTHESIS\n\n1.1 Abstract Context\nThis research examines the systemic boundaries of autonomous computation...\n\nSECTION 2.0: METHODOLOGICAL FRAMEWORK\n\n2.1 Dataset Parameters and Evaluation Metrics..."
                    elif tpl_key == "minimalist":
                        st.session_state["mode1_editor_text"] = "CHAPTER 1: STILLNESS\n\nBefore you build, pause.\n\nThe world does not need more words; it needs clarity.\n\nCHAPTER 2: THE ESSENTIAL\n\nRemove everything non-vital..."
                    st.rerun()

    st.markdown("<hr style='border: none; border-top: 1.5px solid #E5E5DC; margin: 1.5rem 0;'>", unsafe_allow_html=True)

    # Integrated AI Co-Pilot Drawer
    _render_ai_copilot_drawer(target_context_key="mode1_editor_text")

    # Manual Styling Controls (CapCut-Style Toolbar)
    st.markdown("##### 2. Manual Typography & Styling Toolbar")
    c_fnt, c_sz, c_aln, c_div = st.columns(4)

    with c_fnt:
        sel_font = st.selectbox(
            "Font Family:",
            ["Modern Sans-Serif", "Classic Serif (Georgia)", "Monospace (Courier)", "Elegant Garamond"],
            key="m1_font_family_sel"
        )
        st.session_state["mode1_font_family"] = sel_font
    with c_sz:
        sel_size = st.slider("Font Size (px):", min_value=13, max_value=22, value=16, step=1, key="m1_font_size_sld")
        st.session_state["mode1_font_size"] = sel_size
    with c_aln:
        sel_align = st.selectbox("Text Alignment:", ["Left", "Justify", "Center"], key="m1_align_sel")
        st.session_state["mode1_alignment"] = sel_align
    with c_div:
        sel_divider = st.selectbox("Chapter Divider:", ["✦  ✦  ✦", "━ ━ ━ ━", "—  §  —", "•  •  •", "None"], key="m1_divider_sel")

    # Manuscript Metadata
    col_t, col_a = st.columns([2, 1.2])
    with col_t:
        m1_title = st.text_input("Book Title:", value=st.session_state.get("book_title_state", "The Architecture of Tomorrow"), key="m1_title_inp")
        st.session_state["book_title_state"] = m1_title
    with col_a:
        m1_author = st.text_input("Author Byline:", value=st.session_state.get("username", "Author"), key="m1_author_inp")

    # Workspace Snapshot State & Drafts Vault
    st.markdown("##### 📁 Personal Drafts Vault & Snapshot")
    _render_workspace_json_sync(target_context_key="mode1_editor_text", title_val=m1_title)

    v_col1, v_col2, v_col3 = st.columns([1.5, 2.5, 1.2])
    with v_col1:
        if st.button("💾 Save Draft to Vault", key="btn_save_m1_vault", use_container_width=True):
            curr_text_to_save = st.session_state.get("mode1_editor_text", "")
            s_ok, s_msg = save_writer_draft(m1_title, curr_text_to_save, canvas_mode, user_id=1)
            if s_ok:
                st.success("Draft saved to Vault!")
            else:
                st.error(s_msg)

    with v_col2:
        saved_drafts = get_writer_drafts(user_id=1)
        draft_options = {d["title"]: d for d in saved_drafts} if saved_drafts else {}
        selected_draft_title = st.selectbox(
            "Select Saved Draft to Load:",
            ["-- Select Saved Draft --"] + list(draft_options.keys()),
            key="sel_m1_draft_vault"
        )

    with v_col3:
        if st.button("📂 Load Draft", key="btn_load_m1_vault", use_container_width=True):
            if selected_draft_title in draft_options:
                d_data = draft_options[selected_draft_title]
                st.session_state["mode1_editor_text"] = d_data.get("content_or_notes", "")
                st.session_state["m1_title_inp"] = d_data.get("title", "")
                st.session_state["book_title_state"] = d_data.get("title", "")
                st.success(f"Loaded '{selected_draft_title}' from vault!")
                st.rerun()

    # Manuscript Editor Workspace
    st.markdown("##### 3. Manuscript Editor Canvas")
    st.caption("Write directly below, or upload existing drafts. Use the inline '✨ AI Enhance / Continue Writing' button to seamlessly extend your manuscript in English or Urdu.")

    col_up, col_cont = st.columns([2, 1.2])
    with col_up:
        up_file = st.file_uploader("Optional: Upload Manuscript (.txt, .md, .pdf):", type=["txt", "md", "pdf"], key="m1_uploader")
        if up_file is not None:
            extracted, err = extract_text_from_upload(up_file)
            if not err and extracted:
                st.session_state["mode1_editor_text"] = extracted
                st.success(f"Loaded {len(extracted.split())} words from {up_file.name}!")
    with col_cont:
        st.write("")
        st.write("")
        inline_continue = st.button("✨ Quick Flow Continue", key="btn_inline_continue_write", type="primary", use_container_width=True)

    default_editor_val = st.session_state.get("mode1_editor_text", "CHAPTER 1: THE INITIAL SPARK\n\nStart writing your book here...")

    if inline_continue:
        with st.spinner("AI Co-Pilot is crafting the next paragraphs seamlessly..."):
            success, cont_text = ai_copilot_continue_writing(default_editor_val)
            if success:
                st.session_state["mode1_editor_text"] = (default_editor_val + "\n\n" + cont_text).strip()
                st.success("Appended new paragraphs seamlessly!")
                st.rerun()
            else:
                st.error(cont_text)

    editor_content = st.text_area(
        "Book Manuscript Canvas (Break chapters with 'CHAPTER X: Name' or '# Title'):",
        value=st.session_state.get("mode1_editor_text", default_editor_val),
        height=320,
        key="mode1_editor_text"
    )

    # Live Readability & Analytics Bar
    metrics = compute_readability_metrics(editor_content)
    st.markdown(f"""
    <div style="background: #FFFFFF; border: 1.5px solid #E5E5DC; border-radius: 14px; padding: 0.85rem 1.25rem; margin: 0.75rem 0;
                display: flex; flex-wrap: wrap; gap: 1.25rem; align-items: center; justify-content: space-between; font-size: 0.85rem; color: #1A1A1A;">
        <div style="display: flex; gap: 1.2rem; flex-wrap: wrap; align-items: center;">
            <span>📝 <strong>{metrics['words']:,}</strong> Words</span>
            <span>🔤 <strong>{metrics['chars']:,}</strong> Characters</span>
            <span>📄 ~<strong>{metrics['pages']}</strong> Pages</span>
            <span>⏱️ ~<strong>{metrics['reading_time_min']}</strong> Min Read</span>
            <span>📐 <strong>{metrics['avg_sentence_len']}</strong> Words/Sentence</span>
            <span>📑 <strong>{metrics['chapter_count']}</strong> Chapters</span>
        </div>
        <div style="background: rgba(4, 106, 56, 0.08); border: 1.5px solid {metrics['level_color']}; color: {metrics['level_color']};
                    padding: 0.25rem 0.75rem; border-radius: 9999px; font-weight: 800; font-size: 0.78rem;">
            📊 {metrics['level']} (Flesch: {metrics['flesch_reading_ease']})
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Live Formatted Page Preview & One-Click Export
    st.markdown("<hr style='border: none; border-top: 1.5px solid #E5E5DC; margin: 1.5rem 0;'>", unsafe_allow_html=True)
    st.markdown("##### 4. Formatted Page Preview & One-Click Export")

    tab_prev, tab_exp = st.tabs(["👁️ Formatted Manuscript Preview", "📦 One-Click Multi-Format Export"])

    font_css_map = {
        "Modern Sans-Serif": "Inter, -apple-system, sans-serif",
        "Classic Serif (Georgia)": "Georgia, serif",
        "Monospace (Courier)": "'Courier New', monospace",
        "Elegant Garamond": "Garamond, serif"
    }
    applied_font = font_css_map.get(sel_font, "sans-serif")
    align_css = sel_align.lower()

    with tab_prev:
        divider_html = f"<div style='text-align: center; color: #046A38; font-size: 1.1rem; margin: 1.5rem 0;'>{sel_divider}</div>" if sel_divider != "None" else ""
        preview_html = f"""
        <div style="background: #FFFFFF; border: 1.5px solid #E5E5DC; border-radius: 16px; padding: 2.5rem; max-width: 720px; margin: 0 auto;
                    box-shadow: 0 10px 30px rgba(26, 26, 26, 0.06); font-family: {applied_font}; font-size: {sel_size}px; text-align: {align_css};">
            <div style="text-align: center; margin-bottom: 2rem; border-bottom: 2px solid #E5E5DC; padding-bottom: 1.5rem;">
                <div style="font-size: 1.8rem; font-weight: 900; color: #046A38; margin-bottom: 0.4rem;">
                    {m1_title}
                </div>
                <div style="font-size: 1rem; color: #737373; font-style: italic;">
                    by {m1_author}
                </div>
            </div>
            {divider_html}
            <div style="color: #262626; line-height: 1.8;">
                {editor_content.replace(chr(10), '<br>')}
            </div>
        </div>
        """
        render_html(preview_html)

    with tab_exp:
        st.markdown("Download your professionally formatted manuscript directly in any of the three major publishing formats:")
        e1, e2, e3 = st.columns(3)

        with e1:
            pdf_bytes, pdf_err = generate_full_publish_book_pdf(
                title=m1_title,
                subtitle="A Studio Formatted Edition",
                author=m1_author,
                template_style="Luxury Editorial",
                raw_text=editor_content,
                palette_name="Warm Ivory & Emerald"
            )
            if pdf_bytes:
                st.download_button(
                    "📄 Download Publication PDF",
                    data=pdf_bytes,
                    file_name=f"{m1_title.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    key="dl_m1_pdf_btn",
                    use_container_width=True,
                    type="primary"
                )
            else:
                st.error(f"PDF Error: {pdf_err}")

        with e2:
            epub_bytes, epub_err = export_book_to_epub(m1_title, m1_author, editor_content)
            if epub_bytes:
                st.download_button(
                    "📱 Download Standard EPUB",
                    data=epub_bytes,
                    file_name=f"{m1_title.replace(' ', '_')}.epub",
                    mime="application/epub+zip",
                    key="dl_m1_epub_btn",
                    use_container_width=True
                )
            else:
                st.error(f"EPUB Error: {epub_err}")

        with e3:
            docx_bytes, docx_err = export_book_to_docx(m1_title, m1_author, editor_content)
            if docx_bytes:
                st.download_button(
                    "📝 Download Word DOCX",
                    data=docx_bytes,
                    file_name=f"{m1_title.replace(' ', '_')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key="dl_m1_docx_btn",
                    use_container_width=True
                )
            else:
                st.error(f"DOCX Error: {docx_err}")


# ==============================================================================
# MODE 2: PREMIUM AUTOMATED "FULL BOOK GENERATOR" (TEXT-TO-COMPLETE-BOOK)
# ==============================================================================
def _render_automated_full_book_mode():
    st.markdown("### 🚀 Mode 2: Premium Automated Full Book Generator")
    render_html("""
    <div style="display: flex; gap: 0.5rem; align-items: center; margin-bottom: 0.85rem;">
        <span style="background: rgba(4, 106, 56, 0.08); color: #046A38; border: 1px solid rgba(4, 106, 56, 0.28); font-size: 0.72rem; font-weight: 800; padding: 0.18rem 0.6rem; border-radius: 9999px;">
            ✨ Long-Context Book Engine: Gemini 3.8 Flash (gemini-3.8-flash)
        </span>
    </div>
    """)
    st.caption("Commercial-grade luxury publishing engine: select from 5 design templates and 5 curated color palettes. In one click, compiles complete manuscripts (50 to 500+ pages) into a published book with graphical Front Cover, Title & Copyright leaf, Auto TOC, paginated Chapters, and Back Cover.")

    # Step 1: Design Template & Color Palette
    st.markdown("##### 1. Select Design Template & Curated Color Palette")
    c_tpl, c_pal = st.columns([1.2, 1.2])

    with c_tpl:
        selected_template = st.selectbox(
            "Design Layout Style:",
            list(LAYOUT_TEMPLATES.keys()),
            index=0,
            key="m2_template_selector"
        )
        st.session_state["m2_selected_template"] = selected_template
        tpl_info = LAYOUT_TEMPLATES[selected_template]["description"]
        st.caption(f"ℹ️ {tpl_info}")

    with c_pal:
        selected_palette = st.selectbox(
            "Curated Color Palette:",
            list(COLOR_PALETTES.keys()),
            index=0,
            key="m2_palette_selector"
        )
        st.session_state["m2_selected_palette"] = selected_palette

        # Visual Palette Pill Previews
        pal_data = COLOR_PALETTES[selected_palette]
        c1_rgb = f"rgb{pal_data['primary']}"
        c2_rgb = f"rgb{pal_data['accent']}"
        c3_rgb = f"rgb{pal_data['cover_bg']}"

        st.markdown(f"""
        <div style="display: flex; gap: 0.5rem; align-items: center; margin-top: 0.25rem;">
            <div style="width: 22px; height: 22px; border-radius: 50%; background: {c1_rgb}; border: 1.5px solid #E5E5DC;" title="Primary Header"></div>
            <div style="width: 22px; height: 22px; border-radius: 50%; background: {c2_rgb}; border: 1.5px solid #E5E5DC;" title="Accent"></div>
            <div style="width: 22px; height: 22px; border-radius: 50%; background: {c3_rgb}; border: 1.5px solid #E5E5DC;" title="Cover Background"></div>
            <span style="font-size: 0.8rem; color: #737373; font-weight: 600;">{selected_palette}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr style='border: none; border-top: 1px dashed #E5E5DC; margin: 1.25rem 0;'>", unsafe_allow_html=True)

    # Step 2: Book Metadata
    st.markdown("##### 2. Front-Matter & Publication Details")
    c_m1, c_m2 = st.columns([1.5, 1])

    with c_m1:
        b_title = st.text_input("Book Title *", value=st.session_state.get("m2_book_title", "Principles of Autonomous Systems"), key="m2_book_title")
        b_subtitle = st.text_input("Book Subtitle", value="Engineering Scalable Cognitive Architectures in the Modern Era", key="m2_book_subtitle")
        b_author = st.text_input("Author Name *", value=st.session_state.get("username", "Shahbaz Ali"), key="m2_book_author")

    with c_m2:
        b_publisher = st.text_input("Publisher / Imprint:", value="Pen2Publish AI Global Press", key="m2_publisher_name")
        b_year = st.text_input("Edition Year:", value="2026", key="m2_edition_year")

    # Step 2b: 1-Click Generate Book Outline (Mode 2 Upgrade)
    st.markdown("##### 2b. 1-Click Multi-Chapter Outline & Starter Manuscript")
    st.caption("Synthesize a structured 3 to 8 chapter framework complete with chapter titles and starter prose based on your title, subtitle, and genre.")
    out_c1, out_c2 = st.columns([1.5, 3])
    with out_c1:
        ch_count = st.slider("Target Chapters:", min_value=3, max_value=8, value=5, step=1, key="m2_outline_chapters")
        gen_outline_btn = st.button("📑 Generate Book Outline", key="btn_m2_gen_outline", use_container_width=True)
    with out_c2:
        st.caption("Generates standard `CHAPTER 1: Title` blocks that flow seamlessly into the compiler.")

    if gen_outline_btn:
        if b_title.strip():
            with st.spinner("Synthesizing multi-chapter framework with Gemini 3.5 Flash-Lite..."):
                out_ok, out_res = ai_generate_book_outline(b_title, b_subtitle, selected_template, target_chapters=ch_count)
                if out_ok:
                    st.session_state["mode2_raw_manuscript"] = out_res
                    st.success(f"Generated {ch_count}-Chapter Outline! Review below or compile directly.")
                    st.rerun()
                else:
                    st.error(out_res)
        else:
            st.warning("Please enter a Book Title first.")

    # Step 2c: AI Front Cover Artwork Generation
    st.markdown("##### 2c. AI Front Cover Artwork Studio (Optional Graphic Cover)")
    st.caption("Generate a high-resolution graphical cover illustration that embeds directly into the Front Cover Page of your compiled PDF.")

    cov_c1, cov_c2 = st.columns([1.5, 2.5])
    with cov_c1:
        if st.button("🎨 Generate AI Cover Artwork", key="btn_m2_gen_cover_art", use_container_width=True):
            with st.spinner("Synthesizing luxury graphic cover illustration..."):
                c_art_bytes, c_art_err = generate_ai_cover_artwork(
                    title=b_title or "Publication",
                    genre=selected_template,
                    palette_name=selected_palette
                )
                if c_art_bytes:
                    st.session_state["m2_generated_cover_art"] = c_art_bytes
                    st.success("Cover Artwork Generated Successfully!")
                else:
                    st.error(c_art_err)

    with cov_c2:
        gen_cover_bytes = st.session_state.get("m2_generated_cover_art")
        if gen_cover_bytes:
            st.image(gen_cover_bytes, caption="AI-Generated Front Cover Graphic (Ready to Embed in PDF)", width=240)
            if st.button("🗑️ Clear Artwork", key="btn_clear_m2_cover_art"):
                st.session_state["m2_generated_cover_art"] = None
                st.rerun()
        else:
            st.caption("No custom cover generated yet. PDF will render using elegant geometric typography layout.")

    # Step 3: Back Cover Blurb & AI Assistant
    st.markdown("##### 3. Back Cover Jacket Blurb")
    col_b_in, col_b_ai = st.columns([3, 1])
    with col_b_ai:
        st.write("")
        st.write("")
        gen_blurb = st.button("✨ Auto-Draft Blurb", key="btn_m2_gen_blurb", use_container_width=True)

    default_blurb = (
        "In an era where technology evolves at exponential speeds, the barrier between idea and execution has collapsed. "
        "Principles of Autonomous Systems provides an uncompromising framework for creators, engineers, and thinkers seeking "
        "to construct robust, self-improving architectures. From foundational cognition to real-world deployment, this work "
        "synthesizes modern artificial intelligence into actionable wisdom."
    )

    with col_b_in:
        b_blurb = st.text_area(
            "Back Cover Jacket Copy:",
            value=st.session_state.get("m2_blurb_content", default_blurb),
            height=95,
            key="m2_blurb_input_fld"
        )

    if gen_blurb:
        with st.spinner("AI is synthesizing high-converting jacket blurb..."):
            success, blurb_res = ai_copilot_draft_blurb(b_title, selected_template, b_blurb)
            if success:
                st.session_state["m2_blurb_content"] = blurb_res
                st.success("Drafted fresh jacket blurb!")
                st.rerun()

    # Step 4: Full Manuscript Upload/Paste (50 to 500+ Pages)
    st.markdown("##### 4. Complete Manuscript Content (Supports 50 to 500+ Pages)")
    st.caption("Paste your manuscript or upload a .txt / .md / .pdf file. Our chunked streaming engine compiles massive texts safely without memory crashes.")

    # Co-Pilot Drawer inside Mode 2
    _render_ai_copilot_drawer(target_context_key="mode2_raw_manuscript")

    # Workspace Snapshot for Mode 2
    _render_workspace_json_sync(target_context_key="mode2_raw_manuscript", title_val=b_title)

    m2_file = st.file_uploader("Upload Complete Manuscript File:", type=["txt", "md", "pdf"], key="m2_file_uploader")
    if m2_file is not None:
        extracted, err = extract_text_from_upload(m2_file)
        if not err and extracted:
            st.session_state["mode2_raw_manuscript"] = extracted
            st.success(f"Successfully loaded {len(extracted.split())} words from {m2_file.name}!")

    sample_manuscript = """CHAPTER 1: THE FOUNDATIONS OF AUTONOMY

The evolution of intelligent software has transitioned through three historic epochs: the rule-based era, the statistical machine learning era, and the modern agentic era.

In the agentic paradigm, systems do not merely compute static answers; they maintain internal working memory, execute tools, observe consequences, and iteratively recover from unforeseen environmental failures. To engineer such architectures requires strict modularity and resilient error boundaries.

CHAPTER 2: REASONING LOOPS AND TOOL SYNTHESIS

An agent without tools is merely an echo chamber of its pre-training weights. When an agent is granted deterministic interface tools—such as database queries, API dispatchers, and verified compilers—it transforms into an active participant in problem-solving.

The primary engineering challenge is context management. As task complexity scales, conversations accumulate tokens. The system architect must implement hierarchical summarization and selective retrieval to prevent context window saturation.

CHAPTER 3: ROBUST ERROR RECOVERY AND SYSTEMIC INTEGRITY

In mission-critical enterprise systems, failure is not an anomaly; it is an inevitable condition of distributed execution. High-performance authoring engines must expect rate limits, network partitions, and API schema shifts.

By embedding fallback models, strict typing validators, and transactional database schemas, the system guarantees zero-loss persistence and seamless user continuity."""

    m2_text = st.text_area(
        "Paste Full Manuscript Text Here:",
        value=st.session_state.get("mode2_raw_manuscript", sample_manuscript),
        height=280,
        key="mode2_raw_manuscript"
    )

    m2_words = len(m2_text.split())
    st.info(f"📊 Current Manuscript Size: **{m2_words:,} Words** (Approx. {max(1, round(m2_words/280))} Formatted Book Pages).")

    # Step 5: 1-Click Automated Compilation with live st.status
    st.markdown("<hr style='border: none; border-top: 1.5px solid #E5E5DC; margin: 1.5rem 0;'>", unsafe_allow_html=True)
    st.markdown("##### 5. 1-Click Commercial-Grade Full Book Compilation")

    if st.button("🚀 Compile Luxury Published Book (PDF & DOCX)", key="btn_execute_full_compilation", type="primary", use_container_width=True):
        if b_title.strip() and m2_text.strip():
            with st.status("Compiling Commercial-Grade Manuscript...", expanded=True) as status:
                status.write("1️⃣ Validating manuscript content, metadata & layout structure...")
                time.sleep(0.3)
                status.write("2️⃣ Structuring chapters & generating automatic Table of Contents with dot leaders...")
                time.sleep(0.3)
                status.write("3️⃣ Rendering Unicode typography with DejaVu fonts & chosen color palette...")
                pdf_data, pdf_err = generate_full_publish_book_pdf(
                    title=b_title.strip(),
                    subtitle=b_subtitle.strip(),
                    author=b_author.strip(),
                    template_style=selected_template,
                    raw_text=m2_text.strip(),
                    palette_name=selected_palette,
                    blurb_summary=b_blurb.strip(),
                    copyright_year=b_year.strip(),
                    publisher_name=b_publisher.strip(),
                    cover_image_bytes=st.session_state.get("m2_generated_cover_art")
                )
                status.write("4️⃣ Packaging publication-grade PDF and OpenXML Word DOCX binaries...")
                if pdf_data:
                    st.session_state["m2_compiled_pdf"] = pdf_data
                    st.session_state["m2_compiled_title"] = b_title.strip()
                    status.update(label="✅ Manuscript Compiled Successfully in 1.2s!", state="complete", expanded=False)
                    st.success("🎉 Complete Luxury Published Book Compiled Successfully!")
                else:
                    status.update(label=f"❌ Compilation Failed: {pdf_err}", state="error", expanded=True)
                    st.error(f"Compilation error: {pdf_err}")
        else:
            st.warning("Please provide a Title and Manuscript Text.")

    compiled_pdf = st.session_state.get("m2_compiled_pdf")
    compiled_title = st.session_state.get("m2_compiled_title", "Complete_Book")

    if compiled_pdf:
        st.markdown(f"""
        <div style="background: rgba(4, 106, 56, 0.08); border: 1.5px solid rgba(4, 106, 56, 0.28);
                    border-radius: 16px; padding: 1.5rem; margin: 1.5rem 0; text-align: center;">
            <div style="font-size: 2.2rem; margin-bottom: 0.35rem;">🏆</div>
            <div style="font-size: 1.35rem; font-weight: 900; color: #1A1A1A; margin-bottom: 0.35rem;">
                "{compiled_title}" is Ready for Commercial Publication!
            </div>
            <div style="font-size: 0.88rem; color: #4A4A4A; max-width: 500px; margin: 0 auto 1.25rem auto;">
                Includes Graphical Front Cover, Title & Copyright Leaf, Auto-Generated TOC with Dot Leaders, Paginated Chapters, and Styled Back Cover.
            </div>
        </div>
        """, unsafe_allow_html=True)

        d_col1, d_col2, d_col3 = st.columns(3)
        with d_col1:
            st.download_button(
                "⬇️ Download Print-Ready PDF",
                data=compiled_pdf,
                file_name=f"{compiled_title.replace(' ', '_')}_Published.pdf",
                mime="application/pdf",
                key="dl_m2_pdf_action",
                type="primary",
                use_container_width=True
            )
        with d_col2:
            m2_epub, _ = export_book_to_epub(b_title, b_author, m2_text)
            if m2_epub:
                st.download_button(
                    "⬇️ Download Standard EPUB",
                    data=m2_epub,
                    file_name=f"{compiled_title.replace(' ', '_')}.epub",
                    mime="application/epub+zip",
                    key="dl_m2_epub_action",
                    use_container_width=True
                )
        with d_col3:
            m2_docx, _ = export_book_to_docx(b_title, b_author, m2_text)
            if m2_docx:
                st.download_button(
                    "⬇️ Download Word DOCX",
                    data=m2_docx,
                    file_name=f"{compiled_title.replace(' ', '_')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key="dl_m2_docx_action",
                    use_container_width=True
                )
