from __future__ import annotations

from pathlib import Path
from typing import Any, override

import click
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.vectorstores import FAISS
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from pydantic import SecretStr

from langchain_rag_authz.retrievers import AuthzRetriever

PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "human",
            """You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
Question: {input}
Context: {context}
Answer:""",
        ),
    ]
)

docs_loader = DirectoryLoader(
    str(Path(__file__).parent.joinpath("data").resolve(strict=True)), glob="**/*.md", show_progress=True
)
docs = docs_loader.load()

# Add category metadata based on parent directory.
for doc in docs:
    source = doc.metadata.get("source", None)
    assert source
    doc.metadata["category"] = Path(source).parent.name

docs_split = CharacterTextSplitter().split_documents(docs)


class SecretStrParamType(click.ParamType):
    name = "secret"

    @override
    def convert(self, value: Any, param: click.Parameter | None = None, ctx: click.Context | None = None) -> SecretStr:
        if isinstance(value, SecretStr):
            return value

        return SecretStr(value)


SECRET_STR = SecretStrParamType()


@click.command()
@click.option("--user", required=True, help="Unique username to simulate retrieval as.")
@click.option(
    "--authz-token",
    envvar="PANGEA_AUTHZ_TOKEN",
    type=SECRET_STR,
    required=True,
    help="Pangea AuthZ API token. May also be set via the `PANGEA_AUTHZ_TOKEN` environment variable.",
)
@click.option(
    "--pangea-domain",
    envvar="PANGEA_DOMAIN",
    default="aws.us.pangea.cloud",
    show_default=True,
    required=True,
    help="Pangea API domain. May also be set via the `PANGEA_DOMAIN` environment variable.",
)
@click.option("--model", default="gpt-4o-mini", show_default=True, required=True, help="OpenAI model.")
@click.option(
    "--openai-api-key",
    envvar="OPENAI_API_KEY",
    type=SECRET_STR,
    required=True,
    help="OpenAI API key. May also be set via the `OPENAI_API_KEY` environment variable.",
)
@click.argument("prompt")
def main(
    *,
    prompt: str,
    user: str,
    authz_token: SecretStr,
    pangea_domain: str,
    model: str,
    openai_api_key: SecretStr,
) -> None:
    # `user` is assumed to have been previously authenticated by some means.
    # This example will only focus on the AuthZ side of things.

    # Set up vector store
    embeddings_model = OpenAIEmbeddings(api_key=openai_api_key)
    vectorstore = FAISS.from_documents(documents=docs_split, embedding=embeddings_model)

    # Set up a retriever that will filter documents based on the user's
    # permissions in AuthZ.
    retriever = AuthzRetriever(vectorstore=vectorstore, username=user, token=authz_token, domain=pangea_domain)

    llm = ChatOpenAI(model=model, api_key=openai_api_key)
    qa_chain = create_stuff_documents_chain(llm, PROMPT)

    rag_chain = create_retrieval_chain(retriever, qa_chain)

    click.echo(rag_chain.invoke({"input": prompt})["answer"])


if __name__ == "__main__":
    main()
