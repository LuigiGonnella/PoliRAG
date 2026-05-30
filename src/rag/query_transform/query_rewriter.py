from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

class QueryRewriter:
    def __init__(self, llm_api_key: str, llm_base_url: str, llm_model: str):
        self.llm = ChatOpenAI(
            api_key=llm_api_key,
            base_url=llm_base_url,
            model=llm_model,
            temperature=0.0  # Force exact reasoning execution
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "Given a chat history and the latest user question which might reference context in the history, "
                "formulate a standalone question which can be understood without the chat history. "
                "Do NOT answer the question, just reformulate it for an information retrieval system. "
                "Keep it concise and focus on academic keywords."
            )),
            ("placeholder", "{chat_history}"),
            ("human", "{question}")
        ])
        
        self.chain = self.prompt | self.llm

    def run(self, question: str, chat_history: list) -> str:
        try:
            response = self.chain.invoke({"question": question, "chat_history": chat_history})
            return response.content.strip()
        except Exception:
            return question # Resilient fallback to raw user text