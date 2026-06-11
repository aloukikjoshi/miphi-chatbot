from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

_CTX_SYS = (
    "You are a helpful assistant. "
    "Given the conversation history and the user question, "
    "rewrite the question as a standalone question without any prior context. "
    "Do NOT answer. Only rewrite if needed."
)
CONTEXTUALIZE_Q_PROMPT = ChatPromptTemplate.from_messages([
    ("system", _CTX_SYS),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

_QA_SYS = (
    "You are MiPhi\'s intelligent AI assistant. Be professional and friendly.\n\n"
    "When answering:\n"
    "- Use retrieved context if relevant.\n"
    "- Answer from general knowledge if context is empty.\n"
    "- Stay factually positive about MiPhi without inventing claims.\n"
    "- For greetings, respond naturally.\n"
    "- Never reveal confidential information.\n\n"
    "Retrieved context (may be empty):\n{context}"
)
QA_PROMPT = ChatPromptTemplate.from_messages([
    ("system", _QA_SYS),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])
