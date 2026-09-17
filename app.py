import os
import tempfile

import streamlit as st

from src.pdf_loader import extract_text_from_pdf
from src.chunker import create_chunks
from src.embeddings import load_embedding_model, embed_chunks
from src.rag import answer_question


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AI Document Assistant",
    page_icon="✨",
    layout="centered",
)


# =========================================================
# TRANSLATIONS
# =========================================================

TRANSLATIONS = {
    "English": {
        "language": "🌐 Language",
        "subtitle": (
            "Upload your PDF documents and ask questions "
            "in your language. Get grounded answers with "
            "clear sources and page references."
        ),
        "smart_search": "Smart search",
        "sources_badge": "Grounded sources",
        "multilingual": "Multilingual",
        "multiple_pdf": "Multiple PDFs",
        "upload_title": "Upload documents",
        "upload_subtitle": (
            "Upload one or multiple PDF files at the same time."
        ),
        "process": "Process documents",
        "processing": "Reading and analyzing your documents...",
        "success": "document(s) processed successfully.",
        "no_text": (
            "No extractable text was found in any document."
        ),
        "no_text_file": (
            "No extractable text was found in:"
        ),
        "failed_file": "Could not process",
        "processing_error": (
            "An error occurred while processing the documents:"
        ),
        "knowledge_status": "KNOWLEDGE STATUS",
        "ready": "Documents are ready for search",
        "current_documents": "Current documents",
        "documents": "Documents",
        "pages": "Pages",
        "chunks": "Chunks",
        "clear_chat": "Clear chat",
        "start_over": "Start over",
        "chat": "Conversation",
        "question_placeholder": (
            "Ask a question about your documents..."
        ),
        "searching": "Searching your documents...",
        "search_error": (
            "An error occurred while searching:"
        ),
        "sources": "Sources",
        "source": "Source",
        "page": "Page",
        "chunk": "Chunk",
        "no_source": (
            "No relevant source was found in the documents."
        ),
    },

    "Français": {
        "language": "🌐 Langue",
        "subtitle": (
            "Importez vos documents PDF et posez vos questions "
            "dans votre langue. Obtenez des réponses fondées "
            "sur les documents avec leurs sources et pages."
        ),
        "smart_search": "Recherche intelligente",
        "sources_badge": "Sources vérifiées",
        "multilingual": "Multilingue",
        "multiple_pdf": "Plusieurs PDF",
        "upload_title": "Importer des documents",
        "upload_subtitle": (
            "Importez un ou plusieurs fichiers PDF simultanément."
        ),
        "process": "Analyser les documents",
        "processing": "Lecture et analyse des documents...",
        "success": "document(s) traité(s) avec succès.",
        "no_text": (
            "Aucun texte exploitable n'a été trouvé "
            "dans les documents."
        ),
        "no_text_file": (
            "Aucun texte exploitable n'a été trouvé dans :"
        ),
        "failed_file": "Impossible de traiter",
        "processing_error": (
            "Une erreur est survenue pendant l'analyse :"
        ),
        "knowledge_status": "ÉTAT DES DOCUMENTS",
        "ready": "Les documents sont prêts pour la recherche",
        "current_documents": "Documents actuels",
        "documents": "Documents",
        "pages": "Pages",
        "chunks": "Segments",
        "clear_chat": "Effacer la conversation",
        "start_over": "Recommencer",
        "chat": "Conversation",
        "question_placeholder": (
            "Posez une question sur vos documents..."
        ),
        "searching": "Recherche dans les documents...",
        "search_error": (
            "Une erreur est survenue pendant la recherche :"
        ),
        "sources": "Sources",
        "source": "Source",
        "page": "Page",
        "chunk": "Segment",
        "no_source": (
            "Aucune source pertinente n'a été trouvée "
            "dans les documents."
        ),
    },

    "العربية": {
        "language": "🌐 اللغة",
        "subtitle": (
            "ارفع وثائق PDF واسأل عنها بلغتك. "
            "سيبحث المساعد داخل الوثائق ويعطيك "
            "إجابات مدعومة بالمصدر والصفحة."
        ),
        "smart_search": "بحث ذكي",
        "sources_badge": "مصادر موثقة",
        "multilingual": "متعدد اللغات",
        "multiple_pdf": "عدة ملفات PDF",
        "upload_title": "رفع الوثائق",
        "upload_subtitle": (
            "يمكنك رفع ملف PDF واحد أو عدة ملفات في نفس الوقت."
        ),
        "process": "معالجة الوثائق",
        "processing": "جاري قراءة وتحليل الوثائق...",
        "success": "وثيقة تمت معالجتها بنجاح.",
        "no_text": (
            "لم أتمكن من استخراج نص من أي وثيقة."
        ),
        "no_text_file": (
            "لم أجد نصاً قابلاً للاستخراج في:"
        ),
        "failed_file": "تعذر معالجة",
        "processing_error": (
            "حدث خطأ أثناء معالجة الوثائق:"
        ),
        "knowledge_status": "حالة المعرفة",
        "ready": "الوثائق جاهزة للبحث",
        "current_documents": "الوثائق الحالية",
        "documents": "الوثائق",
        "pages": "الصفحات",
        "chunks": "المقاطع",
        "clear_chat": "مسح المحادثة",
        "start_over": "بدء من جديد",
        "chat": "المحادثة",
        "question_placeholder": (
            "اكتب سؤالك حول الوثائق..."
        ),
        "searching": "جاري البحث داخل الوثائق...",
        "search_error": (
            "حدث خطأ أثناء البحث:"
        ),
        "sources": "المصادر",
        "source": "المصدر",
        "page": "الصفحة",
        "chunk": "المقطع",
        "no_source": (
            "لم يتم العثور على مصدر مناسب داخل الوثائق."
        ),
    },
}


# =========================================================
# STYLE
# =========================================================

st.markdown(
    """
<style>

.stApp {
    background:
        linear-gradient(
            180deg,
            #F8F9FD 0%,
            #FFFFFF 55%,
            #F6F7FB 100%
        );
    color: #1E293B;
}

.block-container {
    max-width: 900px;
    padding-top: 1.5rem;
    padding-bottom: 6rem;
}


/* LANGUAGE */

div[data-testid="stSelectbox"] {
    max-width: 210px;
    margin-left: auto;
}

div[data-testid="stSelectbox"] label {
    color: #64748B;
    font-size: 13px;
}


/* HERO */

.hero {
    background:
        linear-gradient(
            135deg,
            #243B53 0%,
            #344B73 48%,
            #7166D8 100%
        );

    border-radius: 26px;
    padding: 38px;
    margin-top: 12px;
    margin-bottom: 32px;

    box-shadow:
        0 18px 45px rgba(36, 59, 83, 0.18);
}

.brand-row {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 17px;
}

.brand-logo {
    width: 54px;
    height: 54px;

    display: flex;
    align-items: center;
    justify-content: center;

    border-radius: 15px;

    background:
        linear-gradient(
            135deg,
            #FFFFFF,
            #E8E5FF
        );

    color: #5B52BE;

    font-size: 19px;
    font-weight: 800;

    box-shadow:
        0 8px 20px rgba(0, 0, 0, 0.14);
}

.brand-title {
    color: #FFFFFF;
    font-size: 32px;
    font-weight: 750;
    line-height: 1.15;
}

.hero-description {
    color: #EEF2FF;
    font-size: 16px;
    line-height: 1.9;
}

.badges {
    margin-top: 22px;
}

.badge {
    display: inline-block;

    background:
        rgba(255, 255, 255, 0.12);

    border:
        1px solid rgba(255, 255, 255, 0.22);

    color: #FFFFFF;

    padding: 8px 13px;
    border-radius: 999px;
    margin: 4px;

    font-size: 12px;
}


/* TITLES */

.section-title {
    color: #243B53;
    font-size: 24px;
    font-weight: 750;
    margin-top: 10px;
    margin-bottom: 6px;
}

.section-subtitle {
    color: #64748B;
    font-size: 14px;
    margin-bottom: 16px;
}


/* UPLOADER */

div[data-testid="stFileUploader"] {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 18px;
    padding: 16px;

    box-shadow:
        0 8px 24px rgba(36, 59, 83, 0.06);
}

div[data-testid="stFileUploaderDropzone"] {
    background: #FAFAFF !important;
    border: 2px dashed #AFA8ED !important;
    border-radius: 14px;
}


/* BUTTONS */

.stButton > button {
    min-height: 45px;
    border-radius: 12px;

    background: #FFFFFF;
    border: 1px solid #D8DCE8;

    color: #243B53;
    font-weight: 650;

    transition: all 0.2s ease;
}

.stButton > button:hover {
    background: #F7F6FF;
    border-color: #7166D8;
    color: #5B52BE;
    transform: translateY(-1px);
}

.stButton > button[kind="primary"] {
    background:
        linear-gradient(
            135deg,
            #536DFE,
            #7C6EE6
        ) !important;

    border: none !important;
    color: #FFFFFF !important;
    font-weight: 750 !important;

    box-shadow:
        0 7px 20px rgba(124, 110, 230, 0.24);
}

.stButton > button[kind="primary"]:hover {
    background:
        linear-gradient(
            135deg,
            #455DE8,
            #695BCF
        ) !important;

    color: #FFFFFF !important;
}


/* INFO CARD */

.info-card {
    background:
        linear-gradient(
            135deg,
            #FFFFFF,
            #FBFAFF
        );

    border: 1px solid #E5E7F2;
    border-left: 4px solid #7C6EE6;

    border-radius: 18px;
    padding: 20px;

    margin-top: 20px;
    margin-bottom: 16px;

    box-shadow:
        0 8px 24px rgba(36, 59, 83, 0.06);
}

.info-title {
    color: #7166D8;
    font-size: 12px;
    font-weight: 750;
    margin-bottom: 8px;
}

.info-value {
    color: #243B53;
    font-size: 17px;
    font-weight: 650;
}


/* DOCUMENT CARD */

.document-card {
    background: #FFFFFF;

    border: 1px solid #E5E7EB;
    border-radius: 14px;

    padding: 13px 16px;
    margin-bottom: 8px;

    color: #334155;

    box-shadow:
        0 4px 14px rgba(36, 59, 83, 0.04);
}


/* CHAT */

div[data-testid="stChatMessage"] {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 18px;

    padding: 12px;
    margin-bottom: 12px;

    box-shadow:
        0 5px 18px rgba(36, 59, 83, 0.05);
}


/* SOURCES */

div[data-testid="stExpander"] {
    background: #FAFAFF;
    border: 1px solid #E6E3FA;
    border-radius: 13px;
}

div[data-testid="stExpander"] summary {
    color: #5B52BE !important;
}


/* DIVIDER */

hr {
    border: none;
    height: 1px;

    background:
        linear-gradient(
            90deg,
            transparent,
            #DDE1EA,
            transparent
        );

    margin-top: 26px;
    margin-bottom: 26px;
}


#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

</style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# FUNCTIONS
# =========================================================

@st.cache_resource
def get_embedding_model():
    return load_embedding_model()


def initialize_session_state():
    if "chunks" not in st.session_state:
        st.session_state.chunks = None

    if "embeddings" not in st.session_state:
        st.session_state.embeddings = None

    if "current_files" not in st.session_state:
        st.session_state.current_files = []

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "page_count" not in st.session_state:
        st.session_state.page_count = 0

    if "chunk_count" not in st.session_state:
        st.session_state.chunk_count = 0

    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0

    if "ui_language" not in st.session_state:
        st.session_state.ui_language = "English"


def clear_chat():
    st.session_state.messages = []
    st.rerun()


def reset_application():
    st.session_state.chunks = None
    st.session_state.embeddings = None
    st.session_state.current_files = []
    st.session_state.messages = []
    st.session_state.page_count = 0
    st.session_state.chunk_count = 0
    st.session_state.uploader_key += 1

    st.rerun()


def display_sources(sources, text):
    if not sources:
        st.info(
            text["no_source"]
        )
        return

    st.markdown(
        f"#### 📚 {text['sources']}"
    )

    for index, source in enumerate(
        sources,
        start=1,
    ):
        with st.expander(
            f"{text['source']} {index} · "
            f"{source['file_name']} · "
            f"{text['page']} {source['page']}"
        ):
            st.caption(
                f"{text['chunk']} "
                f"{source['chunk_number']}"
            )

            st.write(
                source["text"]
            )


# =========================================================
# INITIALIZE
# =========================================================

initialize_session_state()


# =========================================================
# LANGUAGE SELECTOR
# =========================================================

language = st.selectbox(
    "🌐 Language",
    ["English", "Français", "العربية"],
    index=[
        "English",
        "Français",
        "العربية",
    ].index(
        st.session_state.ui_language
    ),
)

st.session_state.ui_language = language

text = TRANSLATIONS[language]

direction = (
    "rtl"
    if language == "العربية"
    else "ltr"
)


# =========================================================
# HERO
# =========================================================

st.markdown(
    f"""
<div class="hero" dir="{direction}">

<div class="brand-row">

<div class="brand-logo">
AI
</div>

<div class="brand-title">
AI Document Assistant
</div>

</div>

<div class="hero-description">
{text["subtitle"]}
</div>

<div class="badges">

<span class="badge">
🔎 {text["smart_search"]}
</span>

<span class="badge">
📚 {text["sources_badge"]}
</span>

<span class="badge">
🌍 {text["multilingual"]}
</span>

<span class="badge">
📄 {text["multiple_pdf"]}
</span>

</div>

</div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# UPLOAD
# =========================================================

st.markdown(
    f'<div class="section-title" dir="{direction}">'
    f'📤 {text["upload_title"]}'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    f'<div class="section-subtitle" dir="{direction}">'
    f'{text["upload_subtitle"]}'
    '</div>',
    unsafe_allow_html=True,
)


uploaded_files = st.file_uploader(
    text["upload_title"],
    type=["pdf"],
    accept_multiple_files=True,
    key=f"pdf_uploader_{st.session_state.uploader_key}",
    label_visibility="collapsed",
)


# =========================================================
# PROCESS DOCUMENTS
# =========================================================

if uploaded_files:

    if st.button(
        f"⚡ {text['process']}",
        type="primary",
        use_container_width=True,
    ):

        all_pages = []
        processed_files = []
        skipped_files = []
        failed_files = []

        try:

            with st.spinner(
                text["processing"]
            ):

                for uploaded_file in uploaded_files:

                    temp_path = None

                    try:

                        with tempfile.NamedTemporaryFile(
                            delete=False,
                            suffix=".pdf",
                        ) as temp_file:

                            temp_file.write(
                                uploaded_file.getbuffer()
                            )

                            temp_path = temp_file.name

                        pages = extract_text_from_pdf(
                            temp_path
                        )

                        if not pages:

                            skipped_files.append(
                                uploaded_file.name
                            )

                            continue

                        for page in pages:
                            page["file_name"] = (
                                uploaded_file.name
                            )

                        all_pages.extend(
                            pages
                        )

                        processed_files.append(
                            uploaded_file.name
                        )

                    except Exception as error:

                        failed_files.append(
                            (
                                uploaded_file.name,
                                str(error),
                            )
                        )

                    finally:

                        if (
                            temp_path is not None
                            and os.path.exists(temp_path)
                        ):
                            os.remove(temp_path)


                if not all_pages:

                    st.error(
                        text["no_text"]
                    )

                else:

                    chunks = create_chunks(
                        all_pages
                    )

                    model = get_embedding_model()

                    embeddings = embed_chunks(
                        chunks,
                        model,
                    )

                    st.session_state.chunks = (
                        chunks
                    )

                    st.session_state.embeddings = (
                        embeddings
                    )

                    st.session_state.current_files = (
                        processed_files
                    )

                    st.session_state.page_count = (
                        len(all_pages)
                    )

                    st.session_state.chunk_count = (
                        len(chunks)
                    )

                    st.session_state.messages = []

                    st.success(
                        f"{len(processed_files)} "
                        f"{text['success']}"
                    )


                    if skipped_files:

                        st.warning(
                            text["no_text_file"]
                            + " "
                            + ", ".join(
                                skipped_files
                            )
                        )


                    for file_name, error in failed_files:

                        st.warning(
                            f"{text['failed_file']} "
                            f"{file_name}: "
                            f"{error}"
                        )


        except Exception as error:

            st.error(
                f"{text['processing_error']} "
                f"{error}"
            )


# =========================================================
# READY DOCUMENTS
# =========================================================

if st.session_state.current_files:

    st.markdown(
        f"""
<div class="info-card" dir="{direction}">

<div class="info-title">
{text["knowledge_status"]}
</div>

<div class="info-value">
{text["ready"]} ✅
</div>

</div>
        """,
        unsafe_allow_html=True,
    )


    st.markdown(
        f"#### 📁 {text['current_documents']}"
    )


    for file_name in (
        st.session_state.current_files
    ):

        st.markdown(
            f"""
<div class="document-card" dir="{direction}">
📄 {file_name}
</div>
            """,
            unsafe_allow_html=True,
        )


    st.caption(
        f"{text['documents']}: "
        f"{len(st.session_state.current_files)}"
        f" · {text['pages']}: "
        f"{st.session_state.page_count}"
        f" · {text['chunks']}: "
        f"{st.session_state.chunk_count}"
    )


    col1, col2 = st.columns(2)


    with col1:

        if st.button(
            f"🧹 {text['clear_chat']}",
            use_container_width=True,
        ):
            clear_chat()


    with col2:

        if st.button(
            f"🔄 {text['start_over']}",
            use_container_width=True,
        ):
            reset_application()


    st.divider()


    # =====================================================
    # CHAT
    # =====================================================

    st.markdown(
        f"### 💬 {text['chat']}"
    )


    for message in (
        st.session_state.messages
    ):

        with st.chat_message(
            "user"
        ):
            st.write(
                message["question"]
            )


        with st.chat_message(
            "assistant"
        ):

            st.write(
                message["answer"]
            )

            display_sources(
                message["sources"],
                text,
            )


    question = st.chat_input(
        text["question_placeholder"]
    )


    if question:

        with st.chat_message(
            "user"
        ):

            st.write(
                question
            )


        try:

            with st.chat_message(
                "assistant"
            ):

                with st.spinner(
                    text["searching"]
                ):

                    model = get_embedding_model()

                    result = answer_question(
                        query=question,
                        chunks=(
                            st.session_state.chunks
                        ),
                        embeddings=(
                            st.session_state.embeddings
                        ),
                        embedding_model=model,
                    )


                st.write(
                    result["answer"]
                )

                display_sources(
                    result["sources"],
                    text,
                )


            st.session_state.messages.append(
                {
                    "question": question,
                    "answer": result["answer"],
                    "sources": result["sources"],
                }
            )


        except Exception as error:

            with st.chat_message(
                "assistant"
            ):

                st.error(
                    f"{text['search_error']} "
                    f"{error}"
                )