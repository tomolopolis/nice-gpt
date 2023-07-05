"""Custom chains for LLM"""
from typing import List

from langchain import PromptTemplate
from langchain.base_language import BaseLanguageModel
from langchain.chains.qa_generation.prompt import PROMPT_SELECTOR
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain.schema import Document, BaseOutputParser, T
from langchain.vectorstores.base import VectorStoreRetriever

from medchain.load_env import (
    model_n_ctx,
    n_forward_documents,
    n_retrieve_documents,
    hard_code_response,
    resp_fmt,
)
from medchain.utils import print_HTML


class PlainTextOutputParser(BaseOutputParser):

    def parse(self, text: str) -> T:
        return text

    def get_format_instructions(self):
        return ''


class BaseQA:
    """base class for Question-Answering"""

    def __init__(self, llm: BaseLanguageModel, retriever: VectorStoreRetriever, prompt: PromptTemplate = None):
        self.llm = llm
        self.retriever = retriever
        self.prompt = prompt or self.default_prompt
        self.retriever.search_kwargs = {**self.retriever.search_kwargs, "k": n_forward_documents, "fetch_k": n_retrieve_documents}
        if resp_fmt == 'json':
            self.output_parser = self._json_fmt_prompt()
        elif resp_fmt == 'text':
            self.output_parser = self._plain_text_fmt_prompt()
        else:
            raise NotImplementedError("Unrecognised format - use RESP_FORMAT=json or RESP_FORMAT=text in .env")

    @property
    def default_prompt(self) -> PromptTemplate:
        """the default prompt"""
        return PROMPT_SELECTOR.get_prompt(self.llm)

    def fetch_documents(self, search: str) -> list[Document]:
        """fetch documents from retriever"""
        return self.retriever.get_relevant_documents(search)

    def format_instructions(self) -> str:
        """fetch format instructions"""
        return self.output_parser.get_format_instructions()

    def formatted_prompt(self, input_str) -> str:
        """Returns the final fully formatted prompt just before being sent to the LLM"""
        raise NotImplementedError('Not implemented for BaseQA')

    @staticmethod
    def _json_fmt_prompt():
        """Add structured output parser"""
        return StructuredOutputParser.from_response_schemas([
            ResponseSchema(name='resp_str', description='your response')
        ])

    @staticmethod
    def _plain_text_fmt_prompt() -> str:
        return PlainTextOutputParser()

    def __call__(self, input_str: str) -> dict:
        """ask a question, return results"""
        return {"result": self.llm.predict(self.default_prompt.format_prompt(question=input_str).to_string())}


class StuffQA(BaseQA):
    """custom QA close to a stuff chain
    compared to the default stuff chain which may exceed the context size, this chain loads as many documents as allowed by the context size.
    Since it uses all the context size, it's meant for a "one-shot" question, not leaving space for a follow-up question which exactly contains the previous one.
    """

    @property
    def default_prompt(self) -> PromptTemplate:
        """the default prompt"""
        prompt = f"""{{format_instructions}}

HUMAN:
Answer the question using ONLY the given extracts from (possibly unrelated and irrelevant) documents, not your own knowledge.
If you are unsure of the answer or if it isn't provided in the extracts, answer "Unknown[STOP]".
Conclude your answer with "[STOP]" when you're finished.

Question: {{question}}

--------------
Here are the extracts:
{{context}}

--------------
Remark: do not repeat the question !

ASSISTANT:
"""
        return PromptTemplate(template=prompt, input_variables=["context", "question", "format_instructions"])

    @staticmethod
    def context_prompt_str(documents: list[Document]) -> str:
        """the document's prompt"""
        prompt = "".join(f"Extract {i + 1}: {document.page_content}\n\n" for i, document in enumerate(documents))
        return prompt.strip()

    def _prep_prompt(self, input_str: str) -> (str, List[Document]):
        all_documents, documents = self.fetch_documents(input_str), []
        format_instruc = self.format_instructions()
        for document in all_documents:
            documents.append(document)
            context_str = self.context_prompt_str(documents)
            formatted_prompt = self.prompt.format_prompt(question=input_str, context=context_str,
                                                         format_instructions=format_instruc).to_string()
            if self.llm.get_num_tokens(formatted_prompt) > model_n_ctx - self.llm.dict()["max_tokens"]:
                documents.pop()
                break
        print_HTML("<r>Stuffed {n} documents in the context</r>", n=len(documents))
        context_str = self.context_prompt_str(documents)

        formatted_prompt = self.prompt.format_prompt(question=input_str, context=context_str,
                                                     format_instructions=format_instruc).to_string()
        return formatted_prompt, documents

    def formatted_prompt(self, input_str) -> str:
        formatted_prompt, _ = self._prep_prompt(input_str)
        return formatted_prompt

    def __call__(self, input_str: str) -> dict:
        formatted_prompt, documents = self._prep_prompt(input_str)

        # LLM response:
        if hard_code_response:
            return {"result": hard_code_response, "source_documents": documents}
        else:
            return {"result": self.output_parser.parse(self.llm.predict(formatted_prompt)),
                    "source_documents": documents}


class RefineQA(BaseQA):
    """custom QA close to a refine chain"""

    @property
    def default_prompt(self) -> PromptTemplate:
        """the default prompt"""
        prompt = f"""{{format_instructions}}

HUMAN:
Answer the question using ONLY the given extracts from a (possibly irrelevant) document, not your own knowledge.
If you are unsure of the answer or if it isn't provided in the extract, answer "Unknown[STOP]".
Conclude your answer with "[STOP]" when you're finished.
Avoid adding any extraneous information.

Question:
-----------------
{{question}}

Extract:
-----------------
{{context}}

ASSISTANT:
"""
        return PromptTemplate(template=prompt, input_variables=["context", "question", "format_instructions"])

    @property
    def refine_prompt(self) -> PromptTemplate:
        """prompt to use for the refining step"""
        prompt = f"""{{format_instructions}}

HUMAN:
Refine the original answer to the question using the new (possibly irrelevant) document extract.
Use ONLY the information from the extract and the previous answer, not your own knowledge.
The extract may not be relevant at all to the question.
Conclude your answer with "[STOP]" when you're finished.
Avoid adding any extraneous information.

Question:
-----------------
{{question}}

Original answer:
-----------------
{{previous_answer}}

New extract:
-----------------
{{context}}

Reminder:
-----------------
If the extract is not relevant or helpful, don't even talk about it. Simply copy the original answer, without adding anything.
Do not copy the question.

ASSISTANT:
"""
        return PromptTemplate(template=prompt, input_variables=["context", "question", "previous_answer",
                                                                "format_instructions"])

    def __call__(self, input_str: str) -> dict:
        """ask a question"""
        documents = self.fetch_documents(input_str)
        last_answer, score = None, None
        for i, doc in enumerate(documents):
            print_HTML("<r>Refining from document {i}/{N}</r>", i=i + 1, N=len(documents))
            prompt = self.default_prompt if i == 0 else self.refine_prompt
            if i == 0:
                formatted_prompt = prompt.format_prompt(question=input_str, context=doc.page_content)
            else:
                formatted_prompt = prompt.format_prompt(question=input_str, context=doc.page_content, previous_answer=last_answer)
            last_answer = self.llm.predict(formatted_prompt.to_string())
        return {
            "result": f"{last_answer}",
            "source_documents": documents,
        }
