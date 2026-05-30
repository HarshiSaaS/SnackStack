from langchain_core.documents import Document
from langchain_chroma import Chroma

from data.menu import MENU_CATALOG
from config import embeddings

def build_documents() -> list[Document]:
    docs: list[Document] = []
    for item in MENU_CATALOG:
        content = (
            f"Dish: {item['name']}\n"
            f"Category: {item['category']} | Cuisine: {item['cuisine']}\n"
            f"Price: ₹{item['price']} | Rating: {item['rating']}/5\n"
            f"Dietary: {', '.join(item['dietary_tags']) if item['dietary_tags'] else 'None'}\n"
            f"Description: {item['description']}\n"
            f"Available: {'Yes' if item['available'] else 'No'}"
        )
        docs.append(
            Document(page_content=content, 
                metadata={
                    "id": item["id"],
                    "name": item["name"],
                    "category": item["category"],
                    "price": item["price"],
                },
            ))
    return docs

def build_retriever(k: int = 3):
    docs = build_documents()
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name="snackstack_menu",
    )
    return vectorstore.as_retriever(search_kwargs={"k": k})

menu_retriever = build_retriever()