import os
import tempfile

import streamlit as st

from src.pdf_loader import extract_text_from_pdf
from src.chunker import create_chunks
from src.embeddings import load_embedding_model, embed_chunks
from src.rag import answer_question


st.set_page_config(
    page_title="AI Document Assistant",
    page_icon="📄",
    layout="centered",
)


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


def display_sources(sources):
    if not sources:
        st.info(
            "لم يتم العثور على مصدر مناسب داخل الوثائق."
        )
        return

    st.markdown("#### المصادر")

    for index, source in enumerate(
        sources,
        start=1,
    ):
        with st.expander(
            f"📄 المصدر {index} — "
            f"{source['file_name']} — "
            f"الصفحة {source['page']}"
        ):
            st.caption(
                f"المقطع {source['chunk_number']} "
                f"— Score: {source['score']:.3f}"
            )

            st.write(
                source["text"]
            )


initialize_session_state()


st.title("📄 AI Document Assistant")

st.write(
    "ارفع ملف PDF واحد أو عدة ملفات، "
    "ومن بعد اطرح أسئلة حول محتواها."
)


uploaded_files = st.file_uploader(
    "اختر ملفات PDF",
    type=["pdf"],
    accept_multiple_files=True,
    key=f"pdf_uploader_{st.session_state.uploader_key}",
)


if uploaded_files:

    if st.button(
        "معالجة الملفات",
        type="primary",
    ):
        try:
            all_pages = []
            processed_files = []
            skipped_files = []
            failed_files = []

            with st.spinner(
                "جاري قراءة وتحليل الملفات..."
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
                        "لم أتمكن من استخراج نص "
                        "من أي ملف."
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

                    st.session_state.chunks = chunks
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
                        f"تمت معالجة "
                        f"{len(processed_files)} "
                        f"ملف/ملفات بنجاح."
                    )

                    if skipped_files:
                        st.warning(
                            "لم أجد نصاً قابلاً للاستخراج في: "
                            + ", ".join(skipped_files)
                        )

                    for file_name, error in failed_files:
                        st.warning(
                            f"تعذر معالجة "
                            f"{file_name}: {error}"
                        )

        except Exception as error:
            st.error(
                f"حدث خطأ أثناء معالجة الملفات: "
                f"{error}"
            )


if st.session_state.current_files:

    st.divider()

    st.write(
        f"الملفات الحالية: "
        f"**{len(st.session_state.current_files)}**"
    )

    for file_name in (
        st.session_state.current_files
    ):
        st.write(
            f"📄 {file_name}"
        )

    st.caption(
        f"مجموع الصفحات التي تحتوي على نص: "
        f"{st.session_state.page_count} "
        f"— مجموع المقاطع: "
        f"{st.session_state.chunk_count}"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "🧹 مسح المحادثة",
            use_container_width=True,
        ):
            clear_chat()

    with col2:
        if st.button(
            "🔄 بدء من جديد",
            use_container_width=True,
        ):
            reset_application()

    st.divider()


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
                message["sources"]
            )


    question = st.chat_input(
        "اكتب سؤالك حول الوثائق"
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
                    "جاري البحث داخل الوثائق..."
                ):

                    model = (
                        get_embedding_model()
                    )

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
                    result["sources"]
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
                    f"حدث خطأ أثناء البحث: "
                    f"{error}"
                )