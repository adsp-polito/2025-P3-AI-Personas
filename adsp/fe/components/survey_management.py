from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

import streamlit as st

from adsp.fe.api_client import APIClient
from adsp.fe.state import get_sidebar_visible_personas, reset_management_ui_state


def _set_view(view: str) -> None:
    reset_management_ui_state()
    st.session_state.current_view = view


def _pretty_question_type(value: str) -> str:
    mapping = {
        "multiple_choice": "Multiple Choice",
        "rating": "Rating",
        "open_ended": "Open Ended",
    }
    return mapping.get(str(value), str(value).replace("_", " ").title())


def _sort_by_created_desc(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(items, key=lambda item: str(item.get("created_at", "")), reverse=True)


def _fetch_all_groups(client: APIClient, *, page_size: int = 200) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    first = client.list_groups(page=1, page_size=page_size)
    first_items = first.get("items", []) if isinstance(first, dict) else []
    first_paging = first.get("paging", {}) if isinstance(first, dict) else {}
    if isinstance(first_items, list):
        items.extend(first_items)

    total_pages = int(first_paging.get("total_pages", 1) or 1)
    for page in range(2, total_pages + 1):
        payload = client.list_groups(page=page, page_size=page_size)
        page_items = payload.get("items", []) if isinstance(payload, dict) else []
        if isinstance(page_items, list):
            items.extend(page_items)

    return _sort_by_created_desc(items)


def _fetch_all_surveys(client: APIClient, *, page_size: int = 200) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    first = client.list_surveys(page=1, page_size=page_size)
    first_items = first.get("items", []) if isinstance(first, dict) else []
    first_paging = first.get("paging", {}) if isinstance(first, dict) else {}
    if isinstance(first_items, list):
        items.extend(first_items)

    total_pages = int(first_paging.get("total_pages", 1) or 1)
    for page in range(2, total_pages + 1):
        payload = client.list_surveys(page=page, page_size=page_size)
        page_items = payload.get("items", []) if isinstance(payload, dict) else []
        if isinstance(page_items, list):
            items.extend(page_items)

    return _sort_by_created_desc(items)


def _parse_rating_scale(question: Dict[str, Any]) -> tuple[int, int]:
    metadata = question.get("metadata", {}) if isinstance(question, dict) else {}
    scale = metadata.get("scale") if isinstance(metadata, dict) else None
    if isinstance(scale, str) and "-" in scale:
        left, right = scale.split("-", 1)
        try:
            start = int(left.strip())
            end = int(right.strip())
            if start < end:
                return start, end
        except Exception:
            return 1, 5
    return 1, 5


def _composition_text(composition: List[Dict[str, Any]]) -> str:
    if not composition:
        return "No composition"
    parts: List[str] = []
    for item in composition:
        persona_id = str(item.get("persona_id", ""))
        count = item.get("count", 0)
        parts.append(f"{persona_id}: {count}")
    return ", ".join(parts)


def _render_paging_controls(
    *,
    prefix: str,
    page: int,
    total_pages: int,
    page_state_key: str,
) -> None:
    total_pages = max(1, int(total_pages or 1))
    page = max(1, min(page, total_pages))

    col_prev, col_pages, col_next = st.columns([1, 6, 1])
    with col_prev:
        if st.button("←", key=f"{prefix}_prev", disabled=page <= 1, width="stretch"):
            reset_management_ui_state()
            st.session_state[page_state_key] = page - 1
            st.rerun()

    with col_pages:
        max_visible = 7
        start = max(1, page - 3)
        end = min(total_pages, start + max_visible - 1)
        start = max(1, end - max_visible + 1)

        cols = st.columns(max(1, end - start + 1))
        for idx, page_num in enumerate(range(start, end + 1)):
            with cols[idx]:
                label = f"[{page_num}]" if page_num == page else str(page_num)
                if st.button(label, key=f"{prefix}_page_{page_num}", width="stretch"):
                    reset_management_ui_state()
                    st.session_state[page_state_key] = page_num
                    st.rerun()

    with col_next:
        if st.button("→", key=f"{prefix}_next", disabled=page >= total_pages, width="stretch"):
            reset_management_ui_state()
            st.session_state[page_state_key] = page + 1
            st.rerun()


def render_create_group_page(client: APIClient) -> None:
    """Render respondent group creation page."""
    st.subheader("Create Respondent Group")

    personas = get_sidebar_visible_personas(client.list_personas())
    countries = client.list_available_countries()

    if not personas:
        st.warning("No personas available")
        return

    with st.form("create_group_form"):
        st.markdown("#### Persona Composition")
        st.caption("Choose how many respondents to generate for each persona.")

        counts: Dict[str, int] = {}
        for persona in personas:
            persona_id = str(persona.get("persona_id", "")).strip()
            persona_name = str(persona.get("persona_name", persona_id)).strip()
            if not persona_id:
                continue
            counts[persona_id] = st.number_input(
                persona_name,
                min_value=0,
                value=0,
                step=1,
                key=f"group_count_{persona_id}",
            )

        st.markdown("#### Countries")
        country_ids = [str(item.get("country_id", "")).strip() for item in countries if item.get("country_id")]
        country_name_by_id = {
            str(item.get("country_id", "")).strip(): str(item.get("display_name", item.get("country_id", ""))).strip()
            for item in countries
            if item.get("country_id")
        }
        selected_country_ids = st.multiselect(
            "Countries",
            options=country_ids,
            format_func=lambda country_id: country_name_by_id.get(country_id, country_id),
            default=[],
            help="Leave empty to assign at random.",
        )

        st.markdown("#### Generation Settings")
        include_names = st.checkbox(
            "Include names",
            value=True,
            help="Generate names for each respondent, otherwise group ID is used as name.",
        )
        mode = st.selectbox("Mode", options=["random", "llm"], index=0)
        sampling_ratio = st.slider(
            "Sampling Ratio",
            min_value=0.1,
            max_value=1.0,
            value=0.7,
            step=0.05,
        )

        col_submit, col_cancel = st.columns(2)
        with col_submit:
            submit = st.form_submit_button("Create Group", type="primary", width="stretch")
        with col_cancel:
            cancel = st.form_submit_button("Cancel", width="stretch")

    if cancel:
        _set_view("chat")
        st.rerun()

    if submit:
        composition = [
            {"persona_id": persona_id, "count": int(count)}
            for persona_id, count in counts.items()
            if int(count) > 0
        ]
        if not composition:
            st.error("Set a positive respondent count for at least one persona.")
            return

        payload_countries = [country_id for country_id in selected_country_ids if country_id in country_name_by_id]

        with st.spinner("Creating respondent group..."):
            created = client.create_group(
                composition=composition,
                mode=mode,
                sampling_ratio=float(sampling_ratio),
                include_names=bool(include_names),
                countries=payload_countries or None,
            )

        if not created:
            st.error("Unable to create respondent group. Please verify API status and payload.")
            return

        st.success(f"Respondent group created: {created.get('group_id', 'unknown')}")
        st.session_state.selected_group_id = created.get("group_id")
        _set_view("group_detail")
        st.rerun()


def render_groups_list_page(client: APIClient) -> None:
    """Render respondent groups list page with pagination."""
    st.subheader("Respondent Groups")

    page = int(st.session_state.get("groups_page", 1))
    page_size = 10

    all_items = _fetch_all_groups(client)
    total_items = len(all_items)
    total_pages = max(1, math.ceil(total_items / page_size)) if total_items else 1
    page = max(1, min(page, total_pages))
    start = (page - 1) * page_size
    end = start + page_size
    items = all_items[start:end]

    if total_items == 0:
        st.info("No respondent group created so far")
        if st.button("Create Respondent Group", key="groups_empty_create", type="primary"):
            _set_view("groups_create")
            st.rerun()
        return

    for group in items:
        group_id = str(group.get("group_id", ""))
        if not group_id:
            continue

        title_col, action_col = st.columns([4, 1])
        with title_col:
            st.markdown(f"**{group_id}**")
            st.caption(
                " | ".join(
                    [
                        f"Total respondents: {group.get('total_respondents', 0)}",
                        f"Mode: {group.get('generation_method', 'n/a')}",
                    ]
                )
            )
            st.caption(f"Composition: {_composition_text(group.get('composition', []))}")

        with action_col:
            if st.button("Open", key=f"open_group_{group_id}", width="stretch"):
                st.session_state.selected_group_id = group_id
                _set_view("group_detail")
                st.rerun()

        st.markdown("---")

    _render_paging_controls(
        prefix="groups",
        page=page,
        total_pages=total_pages,
        page_state_key="groups_page",
    )


def _render_json_like(title: str, payload: Any) -> None:
    st.markdown(f"**{title}**")
    if payload is None or payload == "":
        st.caption("n/a")
    else:
        st.json(payload)


def render_group_detail_page(client: APIClient) -> None:
    """Render full respondent group details page."""
    group_id = st.session_state.get("selected_group_id")
    if not group_id:
        st.warning("No group selected")
        return

    col_back, col_refresh = st.columns([1, 1])
    with col_back:
        if st.button("Back to Groups", width="stretch"):
            _set_view("groups_list")
            st.rerun()
    with col_refresh:
        if st.button("Refresh", width="stretch"):
            st.rerun()

    st.subheader(f"Respondent Group: {group_id}")

    payload = client.get_group(group_id, include_full_profiles=True)
    if not payload:
        st.error("Unable to load group details.")
        return

    st.caption(
        " | ".join(
            [
                f"Total respondents: {payload.get('total_respondents', 0)}",
                f"Mode: {payload.get('generation_method', 'n/a')}",
            ]
        )
    )
    st.caption(f"Composition: {_composition_text(payload.get('composition', []))}")

    respondents = payload.get("respondents", [])
    if not respondents:
        st.info("No full respondents available for this group.")
        return

    st.markdown("### Respondents")
    for respondent in respondents:
        respondent_id = respondent.get("respondent_id", "unknown")
        persona_id = respondent.get("persona_id", "n/a")
        name = respondent.get("name")

        with st.expander(f"{respondent_id} | Persona: {persona_id}", expanded=False):
            st.caption(f"Group ID: {group_id}")
            st.caption(f"Persona ID: {persona_id}")
            st.caption(f"Name: {name if name else 'n/a'}")
            _render_json_like("key indicators", respondent.get("key_indicators"))
            _render_json_like("style profile", respondent.get("style_profile"))
            _render_json_like("value frame", respondent.get("value_frame"))
            _render_json_like("reasoning policies", respondent.get("reasoning_policies"))
            _render_json_like("content filters", respondent.get("content_filters"))


def _normalize_question_ids(questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for idx, item in enumerate(questions, start=1):
        payload = dict(item)
        payload["question_id"] = str(idx)
        normalized.append(payload)
    return normalized


def render_create_survey_page(client: APIClient) -> None:
    """Render survey creation page with question builder."""
    st.subheader("Create Survey")

    if "survey_title_draft" not in st.session_state:
        st.session_state.survey_title_draft = ""
    if "survey_description_draft" not in st.session_state:
        st.session_state.survey_description_draft = ""
    if "new_question_type" not in st.session_state:
        st.session_state.new_question_type = "multiple_choice"

    st.session_state.survey_title_draft = st.text_input(
        "Title",
        value=st.session_state.survey_title_draft,
        key="survey_title_input",
    )
    st.session_state.survey_description_draft = st.text_area(
        "Description",
        value=st.session_state.survey_description_draft,
        height=100,
        key="survey_description_input",
    )

    st.markdown("### Questions")

    add_col, type_col = st.columns([1, 2])
    with type_col:
        question_type = st.selectbox(
            "New question type",
            options=["multiple_choice", "rating", "open_ended"],
            index=["multiple_choice", "rating", "open_ended"].index(st.session_state.new_question_type),
            format_func=_pretty_question_type,
            key="new_question_type_select",
        )
    with add_col:
        if st.button("Add Question", type="primary", width="stretch"):
            draft = list(st.session_state.survey_questions_draft)
            question_payload: Dict[str, Any] = {
                "question_id": str(len(draft) + 1),
                "text": "",
                "type": question_type,
            }
            if question_type == "multiple_choice":
                question_payload["options"] = ["Option 1", "Option 2"]
            elif question_type == "rating":
                question_payload["metadata"] = {"scale": "1-5"}
            draft.append(question_payload)
            st.session_state.survey_questions_draft = _normalize_question_ids(draft)
            st.session_state.new_question_type = question_type
            st.rerun()

    questions = list(st.session_state.survey_questions_draft)

    if not questions:
        st.caption("No questions added yet.")

    delete_idx: Optional[int] = None

    for idx, question in enumerate(questions):
        with st.container():
            st.markdown(f"**Question ID:** {idx + 1}")
            q_type = question.get("type", "open_ended")
            st.caption(f"Type: {_pretty_question_type(str(q_type))}")

            q_text = st.text_input(
                "Question",
                value=str(question.get("text", "")),
                key=f"survey_q_text_{idx}",
            )
            questions[idx]["text"] = q_text

            if q_type == "multiple_choice":
                options = [str(opt) for opt in question.get("options", [])]
                if not options:
                    options = ["Option 1"]

                opt_to_delete: Optional[int] = None
                st.caption("Options")
                for opt_idx, option_value in enumerate(options):
                    opt_col, del_col = st.columns([5, 1])
                    with opt_col:
                        options[opt_idx] = st.text_input(
                            f"Option {opt_idx + 1}",
                            value=option_value,
                            key=f"survey_q_{idx}_opt_{opt_idx}",
                        )
                    with del_col:
                        if st.button("Delete", key=f"survey_q_{idx}_opt_del_{opt_idx}"):
                            opt_to_delete = opt_idx

                questions[idx]["options"] = options

                if st.button("Add Option", key=f"survey_q_{idx}_add_opt"):
                    questions[idx]["options"].append(f"Option {len(options) + 1}")
                    st.session_state.survey_questions_draft = questions
                    st.rerun()

                if opt_to_delete is not None and len(options) > 1:
                    del questions[idx]["options"][opt_to_delete]
                    st.session_state.survey_questions_draft = questions
                    st.rerun()

                questions[idx]["options"] = [opt for opt in questions[idx]["options"] if opt.strip()]

            if q_type == "rating":
                questions[idx]["metadata"] = {"scale": "1-5"}
                st.caption("Scale: 1 to 5")

            if st.button("Delete Question", key=f"survey_q_del_{idx}", width="stretch"):
                delete_idx = idx

            st.markdown("---")

    if delete_idx is not None:
        del questions[delete_idx]
        st.session_state.survey_questions_draft = _normalize_question_ids(questions)
        st.rerun()

    st.session_state.survey_questions_draft = _normalize_question_ids(questions)

    submit_col, cancel_col = st.columns(2)
    with submit_col:
        submit = st.button("Create Survey", type="primary", width="stretch")
    with cancel_col:
        cancel = st.button("Cancel", width="stretch")

    if cancel:
        st.session_state.survey_questions_draft = []
        st.session_state.survey_title_draft = ""
        st.session_state.survey_description_draft = ""
        _set_view("chat")
        st.rerun()

    if submit:
        title = st.session_state.survey_title_draft.strip()
        description = st.session_state.survey_description_draft.strip()

        if not title:
            st.error("Title is required.")
            return

        if not st.session_state.survey_questions_draft:
            st.error("Add at least one question.")
            return

        payload_questions: List[Dict[str, Any]] = []
        for question in st.session_state.survey_questions_draft:
            text = str(question.get("text", "")).strip()
            if not text:
                st.error("Each question must have text.")
                return

            q_type = str(question.get("type", "open_ended"))
            item: Dict[str, Any] = {
                "question_id": str(question.get("question_id")),
                "text": text,
                "type": q_type,
            }
            if q_type == "multiple_choice":
                options = [str(opt).strip() for opt in question.get("options", []) if str(opt).strip()]
                if len(options) < 2:
                    st.error("Multiple-choice questions require at least two options.")
                    return
                item["options"] = options
            if q_type == "rating":
                item["metadata"] = {"scale": "1-5"}
            payload_questions.append(item)

        with st.spinner("Creating survey..."):
            created = client.create_survey(
                title=title,
                description=description,
                questions=payload_questions,
            )

        if not created:
            st.error("Unable to create survey. Please verify API status and payload.")
            return

        st.success(f"Survey created: {created.get('survey_id', 'unknown')}")
        st.session_state.survey_questions_draft = []
        st.session_state.survey_title_draft = ""
        st.session_state.survey_description_draft = ""
        st.session_state.selected_survey_id = created.get("survey_id")
        _set_view("survey_detail")
        st.rerun()


def render_surveys_list_page(client: APIClient) -> None:
    """Render surveys list page with pagination."""
    st.subheader("Surveys")

    page = int(st.session_state.get("surveys_page", 1))
    page_size = 10
    all_items = _fetch_all_surveys(client)
    total_items = len(all_items)
    total_pages = max(1, math.ceil(total_items / page_size)) if total_items else 1
    page = max(1, min(page, total_pages))
    start = (page - 1) * page_size
    end = start + page_size
    items = all_items[start:end]

    if total_items == 0:
        st.info("No surveys created so far")
        if st.button("Create Survey", key="surveys_empty_create", type="primary"):
            _set_view("surveys_create")
            st.rerun()
        return

    for survey in items:
        survey_id = str(survey.get("survey_id", ""))
        if not survey_id:
            continue

        title_col, action_col = st.columns([4, 1])
        with title_col:
            st.markdown(f"**{survey.get('title', survey_id)}**")
            st.caption(f"Survey ID: {survey_id}")
            st.caption(f"{survey.get('description', '')}")

        with action_col:
            if st.button("Open", key=f"open_survey_{survey_id}", width="stretch"):
                st.session_state.selected_survey_id = survey_id
                _set_view("survey_detail")
                st.rerun()

        st.markdown("---")

    _render_paging_controls(
        prefix="surveys",
        page=page,
        total_pages=total_pages,
        page_state_key="surveys_page",
    )


def _load_group_options(client: APIClient) -> List[Dict[str, Any]]:
    return _fetch_all_groups(client)


def _render_statistics_payload(stats: Dict[str, Any]) -> None:
    st.markdown("### Simulation Statistics")
    st.caption(
        " | ".join(
            [
                f"Survey ID: {stats.get('survey_id', 'n/a')}",
                f"Simulation ID: {stats.get('simulation_id', 'n/a')}",
                f"Total respondents: {stats.get('total_respondents', 0)}",
                f"Total responses: {stats.get('total_responses', 0)}",
            ]
        )
    )

    questions = stats.get("questions", [])
    if not questions:
        st.caption("No question-level statistics available.")
        return

    for question in questions:
        with st.expander(f"Question {question.get('question_id', '?')}: {question.get('text', '')}", expanded=False):
            st.caption(f"Type: {_pretty_question_type(str(question.get('type', 'n/a')))}")
            st.caption(f"Answered count: {question.get('answered_count', 0)}")
            st.caption(f"Response rate: {question.get('response_rate', 0)}")

            if question.get("choice_distribution"):
                st.markdown("**Choice distribution**")
                st.json(question.get("choice_distribution"))

            if question.get("rating_distribution"):
                st.markdown("**Rating distribution**")
                st.json(question.get("rating_distribution"))
                st.caption(
                    " | ".join(
                        [
                            f"Average: {question.get('rating_average')}",
                            f"Min: {question.get('rating_min')}",
                            f"Max: {question.get('rating_max')}",
                        ]
                    )
                )

            if question.get("type") == "open_ended":
                st.caption(f"Text response count: {question.get('text_response_count', 0)}")
                st.markdown("**Sample text responses**")
                st.json(question.get("sample_text_responses", []))


def render_survey_detail_page(client: APIClient) -> None:
    """Render survey details with simulation actions."""
    survey_id = st.session_state.get("selected_survey_id")
    if not survey_id:
        st.warning("No survey selected")
        return

    back_col, refresh_col = st.columns([1, 1])
    with back_col:
        if st.button("Back to Surveys", width="stretch"):
            _set_view("surveys_list")
            st.rerun()
    with refresh_col:
        if st.button("Refresh", width="stretch"):
            st.rerun()

    payload = client.get_survey(survey_id)
    if not payload:
        st.error("Unable to load survey details.")
        return

    st.subheader(f"Survey: {payload.get('title', survey_id)}")
    st.caption(f"Survey ID: {payload.get('survey_id', survey_id)}")
    st.caption(payload.get("description", ""))

    st.markdown("### Questions")
    questions = payload.get("questions", [])
    for question in questions:
        with st.expander(f"{question.get('question_id', '?')}. {question.get('text', '')}", expanded=False):
            question_type = str(question.get("type", "n/a"))
            st.caption(f"Type: {_pretty_question_type(question_type)}")
            if question.get("options"):
                st.markdown("**Options**")
                for option in question.get("options", []):
                    st.markdown(f"- {option}")
            elif question_type == "rating":
                min_scale, max_scale = _parse_rating_scale(question)
                st.slider(
                    "Accepted range",
                    min_value=min_scale,
                    max_value=max_scale,
                    value=(min_scale, max_scale),
                    disabled=True,
                    key=f"rating_scale_{survey_id}_{question.get('question_id', '?')}",
                )

    st.markdown("---")
    st.markdown("### Simulations")

    if st.button("Run Simulation", type="primary"):
        st.session_state.show_simulation_form = not st.session_state.show_simulation_form
        st.rerun()

    if st.session_state.show_simulation_form:
        with st.container(border=True):
            st.markdown("#### Run Simulation")
            st.text_input("Survey ID", value=survey_id, disabled=True)

            groups = _load_group_options(client)
            group_choices = [
                f"{item.get('group_id', '')} | respondents: {item.get('total_respondents', 0)}"
                for item in groups
                if item.get("group_id")
            ]
            group_lookup = {
                f"{item.get('group_id', '')} | respondents: {item.get('total_respondents', 0)}": item.get("group_id")
                for item in groups
                if item.get("group_id")
            }

            if not group_choices:
                st.warning("No respondent groups available. Create a group first.")
            else:
                selected_group_label = st.selectbox("Respondent Group", options=group_choices)
                background = st.checkbox("Run in background", value=True)

                run_col, cancel_col = st.columns(2)
                with run_col:
                    run_clicked = st.button("Run", key="run_simulation_confirm", type="primary", width="stretch")
                with cancel_col:
                    cancel_clicked = st.button("Cancel", key="run_simulation_cancel", width="stretch")

                if cancel_clicked:
                    st.session_state.show_simulation_form = False
                    st.rerun()

                if run_clicked:
                    selected_group_id = group_lookup.get(selected_group_label)
                    with st.spinner("Running simulation..."):
                        result = client.run_survey_simulation(
                            survey_id=survey_id,
                            group_id=str(selected_group_id),
                            background=background,
                        )

                    if not result:
                        st.error("Simulation request failed.")
                    else:
                        st.success(
                            f"Simulation started: {result.get('simulation_id', 'n/a')} "
                            f"(status: {result.get('status', 'n/a')})"
                        )
                        st.session_state.show_simulation_form = False
                        st.rerun()

    simulations = payload.get("simulations", [])
    if not simulations:
        st.caption("No simulations yet")
        return

    stats_cache_key = f"{survey_id}"
    if stats_cache_key not in st.session_state.survey_stats_cache:
        st.session_state.survey_stats_cache[stats_cache_key] = {}

    for simulation in simulations:
        simulation_id = simulation.get("simulation_id", "")
        if not simulation_id:
            continue

        progress = simulation.get("progress", {}) if isinstance(simulation, dict) else {}
        completed = progress.get("completed", 0)
        pending = progress.get("pending", 0)
        total_for_progress = completed + pending
        progress_ratio = (completed / total_for_progress) if total_for_progress > 0 else 0.0

        with st.container(border=True):
            st.markdown(f"**Simulation ID:** {simulation_id}")
            st.caption(
                " | ".join(
                    [
                        f"Status: {simulation.get('status', 'n/a')}",
                        f"Group ID: {simulation.get('group_id', 'n/a')}",
                        f"Respondents: {simulation.get('total_respondents', 0)}",
                        f"Progress: {completed} completed / {pending} pending",
                    ]
                )
            )
            st.progress(progress_ratio, text=f"Progress: {int(round(progress_ratio * 100))}%")

            action_col_1, action_col_2, action_col_3 = st.columns(3)

            with action_col_1:
                if st.button("Download", key=f"download_sim_{simulation_id}", width="stretch"):
                    st.session_state.show_download_form_simulation_id = simulation_id
                    st.session_state.prepared_download_payload = None
                    st.rerun()

            with action_col_2:
                if st.button("Compute Statistics", key=f"stats_sim_{simulation_id}", width="stretch"):
                    with st.spinner("Computing simulation statistics..."):
                        stats = client.compute_simulation_statistics(
                            survey_id=survey_id,
                            simulation_id=simulation_id,
                        )
                    if stats:
                        st.session_state.survey_stats_cache[stats_cache_key][simulation_id] = stats
                        st.session_state.active_statistics_simulation_id = simulation_id
                        st.success("Statistics ready")
                        st.rerun()
                    st.error("Unable to compute statistics")

            has_cached_stats = simulation_id in st.session_state.survey_stats_cache[stats_cache_key]
            stats_ready = bool(simulation.get("statistics_ready", False))
            with action_col_3:
                if st.button(
                    "View Statistics",
                    key=f"view_stats_sim_{simulation_id}",
                    disabled=not (has_cached_stats or stats_ready),
                    width="stretch",
                ):
                    if not has_cached_stats and stats_ready:
                        with st.spinner("Loading cached statistics..."):
                            stats = client.compute_simulation_statistics(
                                survey_id=survey_id,
                                simulation_id=simulation_id,
                            )
                        if stats:
                            st.session_state.survey_stats_cache[stats_cache_key][simulation_id] = stats
                    st.session_state.active_statistics_simulation_id = simulation_id
                    st.rerun()

            if st.session_state.show_download_form_simulation_id == simulation_id:
                with st.container(border=True):
                    st.markdown("Download Simulation Responses")
                    export_format = st.selectbox(
                        "Format",
                        options=["csv", "json"],
                        index=0,
                        key=f"download_format_{simulation_id}",
                    )
                    prepared = st.session_state.prepared_download_payload
                    needs_fetch = not (
                        isinstance(prepared, dict)
                        and prepared.get("content")
                        and prepared.get("simulation_id") == simulation_id
                        and prepared.get("format") == export_format
                    )
                    if needs_fetch:
                        with st.spinner("Preparing file..."):
                            download_payload = client.download_simulation_responses(
                                survey_id=survey_id,
                                simulation_id=simulation_id,
                                format=export_format,
                            )
                        if download_payload:
                            download_payload["simulation_id"] = simulation_id
                            download_payload["format"] = export_format
                            st.session_state.prepared_download_payload = download_payload
                        else:
                            st.error("Unable to prepare download")

                    download_col, cancel_col = st.columns(2)
                    with cancel_col:
                        if st.button("Cancel", key=f"close_download_{simulation_id}", width="stretch"):
                            st.session_state.show_download_form_simulation_id = None
                            st.session_state.prepared_download_payload = None
                            st.rerun()

                    prepared = st.session_state.prepared_download_payload
                    with download_col:
                        if isinstance(prepared, dict) and prepared.get("content"):
                            st.download_button(
                                label="Download",
                                data=prepared["content"],
                                file_name=str(prepared.get("filename", "responses.csv")),
                                mime=str(prepared.get("content_type", "application/octet-stream")),
                                key=f"download_button_{simulation_id}",
                                use_container_width=True,
                            )

    active_stats_id = st.session_state.get("active_statistics_simulation_id")
    if active_stats_id:
        stats = st.session_state.survey_stats_cache.get(stats_cache_key, {}).get(active_stats_id)
        if isinstance(stats, dict):
            st.markdown("---")
            _render_statistics_payload(stats)
