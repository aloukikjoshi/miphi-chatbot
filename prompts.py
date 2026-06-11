from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# ---------------------------------------------------------------------------
# Prompt 1: Query Contextualization
# ---------------------------------------------------------------------------
# Used by the history-aware retriever step.
# Given the chat history and the latest user question (which may contain
# pronouns or implicit references), it asks the LLM to produce a fully
# self-contained standalone question that the vector retriever can search.
#
# Example:
#   History: "Tell me about MiPhi B100"
#   User:    "What is its warranty?"
#   Output:  "What is the warranty of the MiPhi B100 SSD?"

_CONTEXTUALIZE_Q_SYSTEM = (
    "You are a helpful assistant. "
    "Given the conversation history below and the user's latest question, "
    "rewrite the question as a standalone question that can be understood "
    "without any prior context. "
    "Do NOT answer the question - only rewrite it if needed. "
    "If the question is already self-contained, return it unchanged."
)

CONTEXTUALIZE_Q_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", _CONTEXTUALIZE_Q_SYSTEM),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

# ---------------------------------------------------------------------------
# Prompt 2: QA Generation
# ---------------------------------------------------------------------------
# Used by the document-stuffing QA chain.
# Receives:
#   {context}       - retrieved document chunks from the vector store
#   {chat_history}  - full alternating HumanMessage / AIMessage list
#   {input}         - the current (possibly rewritten) user question

_QA_SYSTEM = (
    "You are MiPhi's intelligent AI assistant. "
    "Be professional, friendly, and conversational.\n\n"
    "When answering:\n"
    "- If the retrieved context below is relevant, use it to answer accurately.\n"
    "- If the context is empty or not relevant, answer from general technical "
    "knowledge - do not force company context where it does not apply.\n"
    "- For comparisons involving MiPhi products, stay factually positive "
    "about MiPhi without inventing unsupported claims.\n"
    "- For greetings or off-topic questions, respond naturally and helpfully.\n"
    "- Keep answers concise, accurate, and well-structured.\n"
    "- Never reveal or fabricate confidential company information.\n\n"
    "Retrieved context (may be empty):\n"
    "{context}"
)

QA_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", _QA_SYSTEM),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)
